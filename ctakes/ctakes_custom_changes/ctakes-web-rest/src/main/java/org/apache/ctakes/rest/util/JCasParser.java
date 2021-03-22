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
package org.apache.ctakes.rest.util;

import org.apache.log4j.Logger;
import org.apache.ctakes.drugner.type.*;
import org.apache.ctakes.rest.service.CuiResponse;
import org.apache.ctakes.typesystem.type.textsem.*;
import org.apache.uima.fit.util.JCasUtil;
import org.apache.uima.jcas.JCas;
import org.apache.uima.jcas.cas.FSList;
import org.apache.uima.jcas.cas.NonEmptyFSList;
import org.apache.uima.jcas.tcas.Annotation;

import java.sql.Array;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;
import java.util.stream.Collectors;


/**
 * Extracts desired Annotations from a jcas, returning information as a map containing {@link CuiResponse}.
 *
 * Created by tmill on 12/20/18.
 */
final public class JCasParser {

   final private List<Class<? extends Annotation>> semClasses;
   
//   final private Connection connection;
//   private Map<String, ArrayList> cuiToBodyRegionMapping = new HashMap<>();
//   private Map<String, List<Object>> listOfCUIFromDB = new HashMap<>();
// 	 private PreparedStatement _selectTermCall;
//	 public  Map<String, String> snomedCustomHier = new HashMap<>();
   
   static final private Logger LOGGER = Logger.getLogger( "JCasParser" );   

   /**
    * Initializes a list indicating which Annotation types are of interest.
 * @throws SQLException 
    */
   public JCasParser() throws SQLException {
      semClasses = Arrays.asList(

            // CUI types:
            DiseaseDisorderMention.class,
            SignSymptomMention.class,
            ProcedureMention.class,
            AnatomicalSiteMention.class,
            MedicationMention.class,

            // Temporal types:
            TimeMention.class,
            DateAnnotation.class,

            // Drug-related types:
            FractionStrengthAnnotation.class,
            DrugChangeStatusAnnotation.class,
            StrengthUnitAnnotation.class,
            StrengthAnnotation.class,
            RouteAnnotation.class,
            FrequencyUnitAnnotation.class,
            MeasurementAnnotation.class,
            
            LabMention.class,
            EventMention.class,
            MedicationEventMention.class
            

      );
      
   }

   /**
    * @param jcas ye olde ...
    * @return A Map, key is annotation class name (type), value is a list of {@link CuiResponse},
    * one for each annotation of interest.
 * @throws SQLException 
    */
   public Map<String, List<Object>> parse( final JCas jcas ) throws SQLException { //throws Exception {

      Map<String, List<CuiResponse>> resp = JCasUtil.select( jcas, Annotation.class ).stream()
                     .filter( a -> semClasses.contains( a.getClass() ) )
                     .map(a -> {	
								try {
									return new CuiResponse(a, jcas);
								} catch (SQLException e) {
									// TODO Auto-generated catch block
									e.printStackTrace();
									return null;
								}
					})
                     .collect( Collectors.groupingBy( CuiResponse::getType ) );
      
      // populate bodyRegion..couldnt figure out how to populate it in CuiReponse
//	   for (Entry<String, List<CuiResponse>> entry : resp.entrySet()) {
//		   List<CuiResponse> cuiResps = entry.getValue();
//		   for (CuiResponse cuiResp : cuiResps) {
//			   // update all concepts with BodyRegion using CUI
//			   for (Map<String, Object> concept : cuiResp.conceptAttributes) {
//				   if (concept.containsKey("bodyRegion")) {
//					   concept.put("bodyRegion", findBodyRegion((String) concept.get("cui")));
////					   break;
//				   }
//			   }
//			   // update all relations' concepts with BodyRegion using CUI
//			   for (Map<String, Object> relation : cuiResp.relations) {
//				   if (relation.containsKey("rel_concept")) {
//					   List<Map<String, Object>> rel_concepts = (ArrayList) relation.get("rel_concept");
//					   for (Map<String, Object> rel_concept : rel_concepts) {
//						   if (relation.containsKey("bodyRegion")) {
//							   rel_concept.put("bodyRegion", findBodyRegion((String) rel_concept.get("cui")));
//						   }
//						   
//					   }
//				   }
//			   }
//		   }		   
//	   }

      
//      storeFoundCuiToDB(connection);
      
      Map<String, List<Object>> pred = new HashMap<>();
      
      List<Object> internalList = new ArrayList<>();

      for (Predicate predicate : JCasUtil.select(jcas, Predicate.class)) {
    	  Map<String, Object> mapHolder = new HashMap<>();
    	  mapHolder.put("text", predicate.getCoveredText());
    	  mapHolder.put("begin", predicate.getBegin());
    	  mapHolder.put("end", predicate.getEnd());
    	  mapHolder.put("frameSet", predicate.getFrameSet());
    	  
    	  ArrayList<Object> s = new ArrayList<>();
    	  
    	  FSList rels = predicate.getRelations();
    	  
    	  int rel_counter = 0;
    	  
    	  while(rels instanceof NonEmptyFSList){
    		Map<String, Object> mapHolderInside = new HashMap<>();
  			NonEmptyFSList node = (NonEmptyFSList) rels;
  			//SemanticRoleRelationFunction((SemanticRoleRelation) node.getHead());
  			SemanticRoleRelation curRel = (SemanticRoleRelation) node.getHead();
  			SemanticArgument curArg =  curRel.getArgument();
  			// System.out.println(curArg.getBegin() + "	" + curArg.getEnd()  + "	" +  curArg.getCoveredText() + "	" + annot1.getFrameSet() + "	" + annot1.getCoveredText());
  			mapHolderInside.put("rel_" + rel_counter + "_begin", curArg.getBegin());
  			mapHolderInside.put("rel_" + rel_counter + "_end", curArg.getEnd());
  			mapHolderInside.put("rel_" + rel_counter + "_text", curArg.getCoveredText());
  			mapHolderInside.put("rel_" + rel_counter + "_argument", curRel.getCategory());
  			
  			// SemanticArgument s = curArg.getRelation().getArgument();
  			// System.out.println("SECOND SEMANTIC ARGUMENT DETAILS: " + s.getBegin() + "	" + s.getEnd()  + "	" +  s.getCoveredText());
  			
  			s.add(mapHolderInside);
  			
  			rels = node.getTail();
    	  }
    	  
    	  mapHolder.put("relations", s);
    	  internalList.add(mapHolder);
      }
      pred.put("Predicates", internalList);
      Map<String, List<Object>> lastMap = new HashMap<>();
      lastMap.putAll((Map<? extends String, ? extends List<Object>>) resp);
      lastMap.putAll(pred);
      return lastMap;
	
   }
   
//   private void storeFoundCuiToDB (final Connection connection) throws SQLException {
//	   String query = "INSERT INTO sources.cui_to_body_region_mapping (cui, body_region) VALUES (?, ?)";
//	   PreparedStatement ps = connection.prepareStatement(query);    
//	   
//	   for (Entry<String, List<Object>> entry : listOfCUIFromDB.entrySet()) {
//	       ps.setString(1, entry.getKey());
//	       Array bodyRegions = connection.createArrayOf("text", entry.getValue().toArray());
//	       ps.setArray(2, bodyRegions);
//	       ps.addBatch();
//	   }
//	   ps.executeBatch();
//
//   }
   
//   static private PreparedStatement createSelectCall( final Connection connection )
//	         throws SQLException {
//	      final String lookupSql = "select\n" + 
//	      		"--	v.cui as hier_cui ,\n" + 
//	      		"--	v.final_ptr as final_ptr , \n" + 
//	      		"	array_agg(lower(v.str) order by nr desc) ptr_to_str" +
//	      		"--	,\n" + 
//	      		"--	array_agg(lower(v.conso_cui) order by nr desc) concat_conso_cui\n" + 
//	      		"	from\n" + 
//	      		"		(\n" + 
//	      		"		select\n" + 
//	      		"			distinct m.cui,\n" + 
//	      		"			m.ptr || '.' || m.aui as final_ptr,\n" + 
//	      		"			c.str,\n" + 
//	      		"			nr ,\n" + 
//	      		"			c.cui as conso_cui\n" + 
//	      		"		from\n" + 
//	      		"			sources.mrhier m\n" + 
//	      		"		left join lateral unnest(string_to_array(m.ptr || '.' || m.aui, '.')) with ordinality as a(word, nr) on\n" + 
//	      		"			true --and m.ptr like 'A3684559.A3323363.A16962310.%'\n" + 
//	      		"		join sources.mrconso c on\n" + 
//	      		"			c.aui = word\n" + 
//	      		"		where\n" + 
//	      		"			m.cui = ? \n" + 
//	      		"		) v\n" + 
//	      		"	group by\n" + 
//	      		"		v.cui,\n" + 
//	      		"		v.final_ptr";
//	      return connection.prepareStatement( lookupSql );
//	}
   
//   public List<Object> lookupCuiBodyRegion ( String cui) throws SQLException {
//	   
//	   List<Object> cuiBodyRegions = new ArrayList<>();
//	   
//	   fillSelectCall( cui );
//       final ResultSet resultSet = _selectTermCall.executeQuery();
//       
//       while ( resultSet.next() ) {
//    	   String[]res = (String[])resultSet.getArray(1).getArray();
//            
//           for (String r : res) {
//        	   if (snomedCustomHier.containsKey(r.toLowerCase().trim())) {
//        		   String v = snomedCustomHier.get(r.toLowerCase().trim());
//        		   if (!cuiBodyRegions.contains(v)) {
//        			   cuiBodyRegions.add(v);
//        			   
//        		   }
//        	   }
//           }
//        }
//       
//       // if we have not found any body region then we gotta stamp it as Other
//       if (cuiBodyRegions.isEmpty()) {
//    	   cuiBodyRegions.add("other");
//       }
//       
//       setListOfCUIFromDB(cui, cuiBodyRegions);
//       
//	return cuiBodyRegions;
//	   
//   }
   
//   private List<Object> findBodyRegion (String cui ) throws SQLException {
//   	// check if CUI exists in CuiToBodyRegionMapping
//   	if (checkCuiExistsInCuiToBodyRegionMapping(cui)) {
//   		return getValueFromCuiToBodyRegionMapping(cui);
//   	} 
//   	// we did not find the value in our mapping so look to see if this value has been obtained in the current run
//   	else if (checkListOfCUIFromDB(cui)) {
//       	return getListOfCUIFromDB(cui);
//       } 
//   	// if value not in mapping or seen in the current run, then go to DB and fetch a record
//   	else {
//       	return lookupCuiBodyRegion(cui);
//       }
//   }
//   
//   
//   private PreparedStatement fillSelectCall( final String cui ) throws SQLException {
//      _selectTermCall.clearParameters();
//      _selectTermCall.setString( 1, cui );
//      return _selectTermCall;
//   }
//   
//   private boolean checkCuiExistsInCuiToBodyRegionMapping (String cui) {
//	   return cuiToBodyRegionMapping.containsKey(cui);
//		   
//   }
//   
//   public List<Object> getValueFromCuiToBodyRegionMapping (String cui) {
//	   return cuiToBodyRegionMapping.get(cui);
//		   
//   }
//
//	public boolean checkListOfCUIFromDB(String cui) {
//		return listOfCUIFromDB.containsKey(cui);
//	}
//	
//	public  List<Object> getListOfCUIFromDB(String cui) {
//		return listOfCUIFromDB.get(cui);
//	}
//	
//	public void setListOfCUIFromDB(String s, List<Object> v) {
//		listOfCUIFromDB.put(s, v);
//	}
}
