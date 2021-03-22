/**
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 * <p>
 * http://www.apache.org/licenses/LICENSE-2.0
 * <p>
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */
package org.apache.ctakes.rest.service;

import org.apache.ctakes.core.pipeline.PipelineBuilder;
import org.apache.ctakes.core.pipeline.PiperFileReader;
import org.apache.ctakes.rest.util.JCasParser;
import org.apache.ctakes.rest.util.UploadFileToS3;
import org.apache.log4j.Logger;
import org.apache.uima.UIMAFramework;
import org.apache.uima.analysis_engine.AnalysisEngine;
import org.apache.uima.analysis_engine.AnalysisEngineDescription;
import org.apache.uima.cas.impl.XmiCasSerializer;
import org.apache.uima.jcas.JCas;
import org.apache.uima.util.JCasPool;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.context.request.async.DeferredResult;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.common.io.Files;


import javax.annotation.PostConstruct;
import javax.servlet.ServletException;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.nio.charset.Charset;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;
import java.util.concurrent.CompletableFuture;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneOffset;

import java.net.UnknownHostException;

/*
 * Rest web service that takes clinical text
 * as input and produces extracted text as output
 * 
 * 
 * some instructions for myself on how to convert a java project into dynamic web project:
 * https://crunchify.com/convert-java-project-to-dynamic-web-project-in-eclipse-environment/
 * 
 */
@RestController
public class CtakesRestController {

	private static final Logger LOGGER = Logger.getLogger(CtakesRestController.class);
	private static final String DEFAULT_PIPER_FILE_PATH = "pipers/default/Default.piper";
	private static final String FULL_PIPER_FILE_PATH = "pipers/ThreadSafeFullPipeline.piper";
	private static final String DEFAULT_PIPELINE = "Default";
	private static final String FULL_PIPELINE = "Full";
	private static final Map<String, PipelineRunner> _pipelineRunners = new HashMap<>();
	
	// DB details
	private static final String DBUSER = System.getenv("POSTGRES_USER"); 
	private static final String DBPSWD = System.getenv("POSTGRES_PASSWORD");	
	private static final String DBURL = "jdbc:postgresql://" + System.getenv("POSTGRES_SERVER") + "/" + DBUSER;
	
	
	private static Integer TOTAL_RUNNING_PROCESSES = 0;
	
	// -1 is because one core will be taken tomcat and rest become available for api calls
	private static final Integer CORE_COUNT = Runtime.getRuntime().availableProcessors() - 2;;
	
	// when server starts total cores and available cores will be same
	private static Integer AVAILABLE_CORES = CORE_COUNT;

	@PostConstruct
	public void init() throws ServletException {
		
		// recommended by AWS: https://docs.aws.amazon.com/sdk-for-java/v2/developer-guide/java-dg-jvm-ttl.html
		// resolve errors such as :
		// Caused by: java.net.UnknownHostException: starfizz-staging.s3.us-west-2.amazonaws.com
		java.security.Security.setProperty("networkaddress.cache.ttl" , "60");	
		
		LOGGER.info("Initializing analysis engines and jcas pools");
//		_pipelineRunners.put(DEFAULT_PIPELINE, new PipelineRunner(DEFAULT_PIPER_FILE_PATH));
		_pipelineRunners.put(FULL_PIPELINE, new PipelineRunner(FULL_PIPER_FILE_PATH));	
		
		// notify lambda that server has started and to give jobs to run, if any
		prepareSQSMessageNotifySQSLambda("onInit");
	}

	@RequestMapping(value = "/analyze", method = RequestMethod.POST)
	@ResponseBody
	public ResponseEntity<?> getAnalyzedJSON(@RequestBody List<Map<String, Object>> obj,
			@RequestParam("pipeline") String pipelineOptParam) throws Exception {

		List<Map<String, Object>> details = obj;

		// TODO: Add business, user and file id combo validation before proceeding

		LOGGER.info("starting...");
		
		if (TOTAL_RUNNING_PROCESSES.equals(CORE_COUNT)) {
			return ResponseEntity
		            .status(HttpStatus.FORBIDDEN)
		            .body("Resource unavailable to process this request");
		}
		
		// update status of the incoming payload to ASSIGNED in ctakes_server_status
		
		for (Map<String, Object> detail : details) {
			ArrayList<Object> fileStateStatus = new ArrayList<Object>();
			fileStateStatus.add(LocalDateTime.ofInstant(Instant.now(), ZoneOffset.UTC));
			
			// ctakes_server_status
			fileStateStatus.add("ASSIGNED");
			
			// split file state id -
			fileStateStatus.add(detail.get("id"));

			// original file id
			fileStateStatus.add(detail.get("fileId"));

			// business id
			fileStateStatus.add(detail.get("businessId"));
			
			updateFileStateStatus(fileStateStatus);
		}	

		DeferredResult<String> deferredResult = new DeferredResult<>();
		CompletableFuture.supplyAsync(() -> run_in_background(details, pipelineOptParam))
				.whenCompleteAsync((result, throwable) -> deferredResult.setResult(result));

		// run_in_background(details, pipelineOptParam);

		LOGGER.info("completed...");

		// return new ResponseEntity<Success>(HttpStatus.OK);
		return ResponseEntity
	            .status(HttpStatus.CREATED)                 
	            .body("Requested accepted");
	    

	}
	
	static private void updateFileStateStatus(ArrayList<Object> fileStateStatus) throws ClassNotFoundException {
		Class.forName("org.postgresql.Driver");
		try (Connection connection = DriverManager.getConnection(DBURL, DBUSER, DBPSWD)) {

			System.out.println("Connected to PostgreSQL database!");
			System.out.println("testing....");
			
			int affectedrows = 0;
			
			String SQL = " UPDATE file_state SET last_modified_instant = ? , ctakes_server_status = ?"
					+ " where id = ? and file_id =? and business_id = ?";
			
			PreparedStatement st = connection.prepareStatement(SQL);
			st.setObject(1, fileStateStatus.get(0));
			st.setObject(2, fileStateStatus.get(1));
			st.setObject(3, fileStateStatus.get(2));
			st.setObject(4, fileStateStatus.get(3));
			st.setObject(5, fileStateStatus.get(4));
			
			affectedrows = st.executeUpdate();

			System.out.print("updateFileStateStatus affectedrows: " + affectedrows);

		} catch (SQLException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}

	public enum ProcessingStatusEnum {
		created, running, completed, fail;
	}

	static private void connect_db(ArrayList<Object> ctakesDbResponse) throws ClassNotFoundException {

		Class.forName("org.postgresql.Driver");
		try (Connection connection = DriverManager.getConnection(DBURL, DBUSER, DBPSWD)) {

			System.out.println("Connected to PostgreSQL database!");
			System.out.println("testing....");

			int affectedrows = 0;

			String SQL = "UPDATE file_state " + "SET ctakes_start_instant = ? , " + "ctakes_json_file_name = ? , "
					+ "ctakes_processing_status = ?::filestateenum , " + "ctakes_user_id = ? , "
					+ "ctakes_completed_instant = ? ," + "ctakes_error_response = ? , " + "last_modified_instant = ? , "
					+ "last_modified_by = ? " + "WHERE id = ? and file_id = ? and business_id = ?";

			PreparedStatement st = connection.prepareStatement(SQL);

			st.setObject(1, ctakesDbResponse.get(0));
			st.setObject(2, ctakesDbResponse.get(1));
			st.setObject(3, ctakesDbResponse.get(2));
			st.setObject(4, ctakesDbResponse.get(3));
			st.setObject(5, ctakesDbResponse.get(4));
			st.setObject(6, ctakesDbResponse.get(5));
			st.setObject(7, ctakesDbResponse.get(4));
			st.setObject(8, ctakesDbResponse.get(3));
			st.setObject(9, ctakesDbResponse.get(6));
			st.setObject(10, ctakesDbResponse.get(7));
			st.setObject(11, ctakesDbResponse.get(8));

			affectedrows = st.executeUpdate();

			System.out.print(affectedrows);

		} catch (SQLException e) {
			System.out.println("Connection failure.");
			e.printStackTrace();
		}
	}
	
	static private String run_in_background(List<Map<String, Object>> details, String pipelineOptParam) {
		
		TOTAL_RUNNING_PROCESSES = TOTAL_RUNNING_PROCESSES + 1;
		AVAILABLE_CORES = CORE_COUNT - TOTAL_RUNNING_PROCESSES;
		System.out.println("Before FOR TOTAL_RUNNING_PROCESSES " + TOTAL_RUNNING_PROCESSES);
		System.out.println("Before FOR AVAILABLE_CORES " + AVAILABLE_CORES);


		for (Map<String, Object> detail : details) {

			ArrayList<Object> ctakesDbResponse = new ArrayList<Object>();
			boolean error_occurred = false;
			String stackTrace = null;

			ctakesDbResponse.add(LocalDateTime.ofInstant(Instant.now(), ZoneOffset.UTC));

			UploadFileToS3 s3FetchExtractTextFile = new UploadFileToS3();

			try {

				String pipeline = DEFAULT_PIPELINE;
				if (pipelineOptParam != null && !pipelineOptParam.isEmpty()) {
					if (FULL_PIPELINE.equalsIgnoreCase(pipelineOptParam)) {
						pipeline = FULL_PIPELINE;
					}
				}
				final PipelineRunner runner = _pipelineRunners.get(pipeline);

				String text = s3FetchExtractTextFile.downloadS3FileToExtractText(detail);

				if ((boolean) detail.get("debug")) {
					System.out.print(text);
				}

				Map<String, List<Object>> a = runner.process(text, detail);

				if ((boolean) detail.get("debug")) {
					System.out.println(a);
				}

			} catch (Exception e) {
				// TODO Auto-generated catch block
				error_occurred = true;
				e.printStackTrace();

				StringWriter sw = new StringWriter();
				PrintWriter pw = new PrintWriter(sw);
				e.printStackTrace(pw);
				pw.flush();
				stackTrace = sw.toString();

			} finally {

				// where json file was stored
				ctakesDbResponse.add(detail.get("extractFileName") + ".json");

				Object d = error_occurred ? ProcessingStatusEnum.fail.toString() : ProcessingStatusEnum.completed.toString();
				detail.put("ctakes_exception", d.toString());

				// record error
				ctakesDbResponse.add(d);

				// user id
				ctakesDbResponse.add(detail.get("userId"));

				// completed timestamp
				ctakesDbResponse.add(LocalDateTime.ofInstant(Instant.now(), ZoneOffset.UTC));

				// record stacktrace if there is any
				ctakesDbResponse.add((stackTrace != null && !stackTrace.isEmpty()) ? stackTrace : null);

				// split file state id -
				ctakesDbResponse.add(detail.get("id"));

				// original file id
				ctakesDbResponse.add(detail.get("fileId"));

				// business id
				ctakesDbResponse.add(detail.get("businessId"));

				try {
					connect_db(ctakesDbResponse);
				} catch (ClassNotFoundException e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
				}

				try {
					s3FetchExtractTextFile.initiateMentionLambda(detail);
				} catch (Exception e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
				}

				System.out.println("Completed in: " + ctakesDbResponse.get(0) + "     " + ctakesDbResponse.get(4));
			}
		}
		
		TOTAL_RUNNING_PROCESSES = TOTAL_RUNNING_PROCESSES - 1;
		AVAILABLE_CORES = CORE_COUNT - TOTAL_RUNNING_PROCESSES;
		
		// notify lambda that a single core has completed a job and ready to process more
		prepareSQSMessageNotifySQSLambda("onCompletion");
		
		System.out.println("AFTER FOR TOTAL_RUNNING_PROCESSES " + TOTAL_RUNNING_PROCESSES);
		System.out.println("AFTER FOR AVAILABLE_CORES " + AVAILABLE_CORES);
		
		return "Task finished.";
	}
	
	static void prepareSQSMessageNotifySQSLambda(String type) {
		UploadFileToS3 s3LetLambdaKnow = new UploadFileToS3();
		
		Map<String, String> sqsMessageObject = new HashMap<>();
		
		sqsMessageObject.put("TOTAL_RUNNING_PROCESSES", String.valueOf(TOTAL_RUNNING_PROCESSES));
		sqsMessageObject.put("AVAILABLE_CORES", String.valueOf(AVAILABLE_CORES));
		sqsMessageObject.put("TOTAL_CPU_CORE_COUNT", String.valueOf(CORE_COUNT));
		sqsMessageObject.put("TYPE", type);
		try {
			sqsMessageObject.put("LOCAL_HOST_NAME", s3LetLambdaKnow.getLocalHostName());
		} catch (UnknownHostException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
			sqsMessageObject.put("LOCAL_HOST_NAME", "UNKNOWN");
		}
		
		try {
			sqsMessageObject.put("LOCAL_IP_ADDRESS", s3LetLambdaKnow.getLocalHostAddress());
		} catch (UnknownHostException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
			sqsMessageObject.put("LOCAL_IP_ADDRESS", "UNKNOWN");
		}
		
		s3LetLambdaKnow.makeLambdaAwareOfAvailableCores(sqsMessageObject, System.getenv("AWS_SQS_Q_NAME")); //queueUrl
	}

	static private void uploadJsontoS3(Map<String, List<Object>> resultMap, Map<String, Object> thisDetails)
			throws Exception {

		UploadFileToS3 a = new UploadFileToS3();

		String json = new ObjectMapper().writeValueAsString(resultMap);

		ByteArrayOutputStream bos = new ByteArrayOutputStream();
		// ObjectOutput out = null;
		//
		// out = new ObjectOutputStream(bos);
		// out.writeObject(json);
		// out.flush();

		OutputStreamWriter in = new OutputStreamWriter(bos, Charset.forName("UTF-8"));
		in.write(json);
		in.flush();

		byte[] yourBytes = bos.toByteArray();

		a.upload(thisDetails, yourBytes);
	}

	static private Map<String, List<Object>> formatResults(JCas jcas) throws Exception {
		JCasParser parser = new JCasParser();
		return parser.parse(jcas);
	}

	static private final class PipelineRunner {
		private final AnalysisEngine _engine;
		private final JCasPool _pool;

		private PipelineRunner(final String piperPath) throws ServletException {
			try {
				PiperFileReader reader = new PiperFileReader(piperPath);
				PipelineBuilder builder = reader.getBuilder();
				AnalysisEngineDescription pipeline = builder.getAnalysisEngineDesc();
				_engine = UIMAFramework.produceAnalysisEngine(pipeline);
				_pool = new JCasPool(10, _engine);
			} catch (Exception e) {
				LOGGER.error("Error loading pipers");
				e.printStackTrace();
				throw new ServletException(e);
			}
		}

		public Map<String, List<Object>> process(final String text, Map<String, Object> allDetails)
				throws ServletException {
			JCas jcas = null;
			Map<String, List<Object>> resultMap = null;
			if (text != null) {
				try {
					jcas = _pool.getJCas(0);
					jcas.setDocumentText(text);
					_engine.process(jcas);

					ByteArrayOutputStream output = new ByteArrayOutputStream();
					XmiCasSerializer.serialize(jcas.getCas(), output);

					// For debugging:
					if ((boolean) allDetails.get("debug")) {
						String outputStr = output.toString();
						Files.write(outputStr.getBytes(), new File("/tmp/TEST__TomCat_Result.xml"));
						;
//						System.out.println(jcas);
//						System.out.println(outputStr.getBytes());
//						System.out.println(outputStr);
					}

					resultMap = formatResults(jcas);
					_pool.releaseJCas(jcas);
				} catch (Exception e) {
					LOGGER.error("Error processing Analysis engine");
					e.printStackTrace();
					throw new ServletException(e);
				}
			}

			try {
				uploadJsontoS3(resultMap, allDetails);
			} catch (Exception e) {
				e.printStackTrace();
				throw new ServletException(e);
			}

			return resultMap;
		}
	}

	@RequestMapping(value = "/health", method = RequestMethod.GET)
	@ResponseBody
	public ResponseEntity<?> getAnalyzedJSON() throws Exception {
		return ResponseEntity
	            .status(HttpStatus.CREATED)                 
	            .body("Requested accepted");
	}

	@RequestMapping(value = "/analyze_local", method = RequestMethod.POST)
	@ResponseBody
	public ResponseEntity<?> getAnalyzedJSON_local_testing(@RequestBody String analysisText,
			@RequestParam("pipeline") String pipelineOptParam, @RequestParam("businessId") String businessId,
			@RequestParam("bucket") String bucket, @RequestParam("source") String source,
			@RequestParam("extractFileName") String destination) throws Exception {

		// System.out.println(pipelineOptParam);
		// System.out.println(businessId);
		// System.out.println(bucket);
		// System.out.println(source);
		// System.out.println(destination);

		Map<String, String> details = new HashMap<>();

		details.put("pipelineOptParam", pipelineOptParam.toString());
		details.put("businessId", businessId);
		details.put("bucket", bucket);
		details.put("source", source);
		details.put("extractFileName", destination);

		// UploadFileToS3 a = new UploadFileToS3();
		//
		// File newFile = a.generateUniqueFileName(details.get("destination"));

		LOGGER.info("starting...");

		// DeferredResult<String> deferredResult = new DeferredResult<>();
		// CompletableFuture.supplyAsync(()-> runslowly(analysisText, details,
		// pipelineOptParam))
		// .whenCompleteAsync((result, throwable) -> deferredResult.setResult(result));

		// connect_db();

		LOGGER.info("completed...");

//		return new ResponseEntity<Success>(HttpStatus.OK);
		
		return ResponseEntity
	            .status(HttpStatus.CREATED)                 
	            .body("Requested accepted");

	}

}
