package org.apache.ctakes.rest.util;

import java.io.UnsupportedEncodingException;
import java.net.InetAddress;
import java.net.UnknownHostException;
import java.util.Map;
import java.util.concurrent.CompletableFuture;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

import software.amazon.awssdk.core.ResponseBytes;
import software.amazon.awssdk.core.SdkBytes;
import software.amazon.awssdk.core.sync.RequestBody;
import software.amazon.awssdk.core.sync.ResponseTransformer;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.GetObjectRequest;
import software.amazon.awssdk.services.s3.model.GetObjectResponse;
import software.amazon.awssdk.services.s3.model.PutObjectRequest;
import software.amazon.awssdk.services.s3.model.PutObjectResponse;

import software.amazon.awssdk.services.lambda.LambdaAsyncClient;
import software.amazon.awssdk.services.lambda.model.InvokeRequest;
import software.amazon.awssdk.services.lambda.model.InvokeResponse;

import software.amazon.awssdk.services.sqs.SqsClient;
import software.amazon.awssdk.services.sqs.model.SendMessageRequest;
import software.amazon.awssdk.services.sqs.model.SendMessageResponse;

public class UploadFileToS3 {

    private static Region region = Region.US_WEST_2;

	
	public void upload(Map<String, Object> thisDetails, byte[] yourBytes) throws Exception {
		
		// TODO: later add aws keys dynamically instead of getting them from environment variables
//		AwsSessionCredentials awsCreds = AwsSessionCredentials.create(
//			      "access_key_id",
//			      "secret_key_id",
//			      "session_token");
//		
//		S3Client s32 = S3Client.builder()
//                .credentialsProvider(StaticCredentialsProvider.create(awsCreds))
//                .build();
		
		S3Client s3;
		s3 = S3Client.builder().region(region).build();
		
		String keyName = thisDetails.get("extractFileName") + ".json";
		
		thisDetails.put("json_file", keyName);
        
		PutObjectResponse response = s3.putObject(PutObjectRequest.builder()
				.bucket((String) thisDetails.get("bucket"))
				.key(keyName)
				.build(), RequestBody.fromBytes(yourBytes));
		
		System.out.println(response);
//		
//		if (java.util.Objects.equals(response.sdkHttpResponse().statusCode(), 200)) {
//			
//			
//		};
		
	}
	
	public void initiateMentionLambda(Map<String, Object> thisDetails) throws Exception {
		LambdaAsyncClient lambda;
		lambda = LambdaAsyncClient.builder().region(region).build();
		
		String json = new ObjectMapper().writeValueAsString(thisDetails);
		
		SdkBytes.fromUtf8String(json);
		
		CompletableFuture<InvokeResponse> lambdaResponse = lambda.invoke(InvokeRequest.builder().functionName(System.getenv("AWS_MENTION_EXTRATOR_LAMBDA")).payload(SdkBytes.fromUtf8String(json)).build());
				
		// CompletableFuture<InvokeResponse> d = lambdaResponse.whenComplete((aVoid, throwable) -> System.out.println("Completed f1"));
		
		System.out.println(lambdaResponse);
		lambdaResponse = null;
		System.gc(); 
	}
	
	public String downloadS3FileToExtractText (Map<String, Object> thisDetails) throws UnsupportedEncodingException, Exception {
		S3Client s3;
		s3 = S3Client.builder().region(region).build();
		ResponseBytes<GetObjectResponse> a = s3.getObject(GetObjectRequest.builder()
				.bucket((String) thisDetails
				.get("bucket"))
				.key((String) thisDetails.get("extractFileName"))
				.build(), ResponseTransformer.toBytes());
        
        String str = new String(a.asByteArray(), "UTF-8");
                
        return str;
	}
	
	public void makeLambdaAwareOfAvailableCores(Map<String, String> sqsMessageObject, String queueUrl) {
		
		String json = null;
		
		try {
			 json = new ObjectMapper().writeValueAsString(sqsMessageObject);
		} catch (JsonProcessingException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		System.out.println(json);
		SqsClient sqsClient;
		sqsClient = SqsClient.builder().region(region).build();
		
		SendMessageResponse d = sqsClient.sendMessage(SendMessageRequest.builder()
		        .queueUrl(queueUrl)
		        .messageBody(json)
		        .delaySeconds(10)
		        .build());
		System.out.print(d);
	}
	
	public String getLocalHostName() throws UnknownHostException {
		InetAddress inetAddress = InetAddress.getLocalHost();
		return inetAddress.getHostName();
	}
	
	public String getLocalHostAddress() throws UnknownHostException {
		InetAddress inetAddress = InetAddress.getLocalHost();
		return inetAddress.getHostAddress();
	}
	
	protected void finalize() throws Throwable 
    { 
        System.out.println("Garbage collector called"); 
        System.out.println("Object garbage collected : " + this); 
    }
	
	
	
	
//	public File generateUniqueFileName (String fileName) throws Exception {
//		
//		String ext = ".json";
//		
//		// String justFileName = fileName.substring(0, fileName.lastIndexOf('/'));
//		
//		String newFileName = "/tmp/" + UUID.randomUUID().toString() + ext;
//		
//		int num = 0;
//		File file = new File(newFileName);
//		
//	     while (file.exists()) {
//			num++;
//	         file = new File(fileName.substring(0, fileName.lastIndexOf('.')) + UUID.randomUUID().toString() + ext);
//	     }
//	     return file;
//		
//	}
}
