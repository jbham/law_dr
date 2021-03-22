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

import org.apache.ctakes.typesystem.type.refsem.Date;
import org.apache.ctakes.typesystem.type.refsem.MedicationDosage;
import org.apache.ctakes.typesystem.type.refsem.MedicationDuration;
import org.apache.ctakes.typesystem.type.refsem.MedicationForm;
import org.apache.ctakes.typesystem.type.refsem.MedicationFrequency;
import org.apache.ctakes.typesystem.type.refsem.MedicationRoute;
import org.apache.ctakes.typesystem.type.refsem.MedicationStatusChange;
import org.apache.ctakes.typesystem.type.refsem.MedicationStrength;
import org.apache.ctakes.typesystem.type.refsem.UmlsConcept;
import org.apache.ctakes.typesystem.type.relation.BinaryTextRelation;
import org.apache.ctakes.typesystem.type.textsem.AnatomicalSiteMention;
import org.apache.ctakes.typesystem.type.textsem.DiseaseDisorderMention;
import org.apache.ctakes.typesystem.type.textsem.IdentifiedAnnotation;
import org.apache.ctakes.typesystem.type.textsem.MedicationDosageModifier;
import org.apache.ctakes.typesystem.type.textsem.MedicationDurationModifier;
import org.apache.ctakes.typesystem.type.textsem.MedicationFormModifier;
import org.apache.ctakes.typesystem.type.textsem.MedicationFrequencyModifier;
import org.apache.ctakes.typesystem.type.textsem.MedicationMention;
import org.apache.ctakes.typesystem.type.textsem.MedicationRouteModifier;
import org.apache.ctakes.typesystem.type.textsem.MedicationStatusChangeModifier;
import org.apache.ctakes.typesystem.type.textsem.MedicationStrengthModifier;
import org.apache.ctakes.typesystem.type.textsem.TimeMention;
import org.apache.uima.fit.util.JCasUtil;
import org.apache.uima.jcas.JCas;
import org.apache.uima.jcas.cas.FSArray;
import org.apache.uima.jcas.tcas.Annotation;

import java.sql.SQLException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import org.apache.ctakes.rest.util.JCasParser;


/**
 * Created by tmill on 12/20/18.
 */
public class CuiResponse{
    final private String _type;
    public int begin;
    public int end;
    public String text;
    public int historyOf;
    public String subject;
    public int polarity;
    public float confidence;
    public int uncertainty;
    public String bodyside;
    public List<Map<String,Object>> medicationDetailsList = new ArrayList<>();
//    public BodyLateralityModifier bodyLaterality ;
    
    public List<Map<String,Object>> conceptAttributes = new ArrayList<>();
    
    
    public List<Map<String, Object>> relations = new ArrayList<>() ;

    public CuiResponse(Annotation annotation, final JCas jcas ) throws SQLException{
        _type = annotation.getClass().getSimpleName();
        begin = annotation.getBegin();
        end = annotation.getEnd();
        text = annotation.getCoveredText();
        
        Boolean anatomyAnnotation = false; 
        
        if (annotation instanceof AnatomicalSiteMention) {
        	anatomyAnnotation = true;
        	AnatomicalSiteMention ia = (AnatomicalSiteMention) annotation;
        	
        	if (ia.getBodySide() != null) {
//        		System.out.println(ia.getBodySide().toString() + ", " + ia.getBodySide());
        		bodyside = ia.getBodySide().getCoveredText();
        	}
        	
//        	bodyLaterality = ia.getBodyLaterality();
        }
        
        if (annotation instanceof DiseaseDisorderMention) {
        	DiseaseDisorderMention ia = (DiseaseDisorderMention) annotation;
        	if (ia.getBodySide() != null) {
        		bodyside = ia.getBodySide().getCoveredText();
        	}        	
//        	bodyLaterality = ia.getBodyLaterality();
        }
        
        if (annotation instanceof MedicationMention) {
        	MedicationMention neAnnot = (MedicationMention) annotation;
        	Map<String,Object> medicationDetails = new HashMap<>();
        	
        	if (neAnnot.getMedicationStrength() != null) {
        		MedicationStrengthModifier strength = neAnnot.getMedicationStrength();
    			MedicationStrength strengthTerm = (MedicationStrength) strength.getNormalizedForm();
    			
    			if (strengthTerm != null) { 
    				String strengthTermString = strengthTerm.getNumber()+ " " +strengthTerm.getUnit();
    				medicationDetails.put("strength", strengthTermString);
    				
    			}
        	}
			
        	if (neAnnot.getMedicationDosage() != null) {
        		MedicationDosageModifier dosageModifier = neAnnot.getMedicationDosage();
    			if (dosageModifier != null) {
    				MedicationDosage d = (MedicationDosage) dosageModifier.getNormalizedForm();
    				if (d!=null) {
    					String medicationDosageString = d.getValue();
    					medicationDetails.put("dosage", medicationDosageString);
    				}
    			}
        	}

        	if (neAnnot.getMedicationFrequency() != null) {
        		MedicationFrequencyModifier freqModifier = neAnnot.getMedicationFrequency();
    			if (freqModifier != null) {
    				MedicationFrequency f = (MedicationFrequency) freqModifier.getNormalizedForm();
    				if (f != null) {
    					String medicationFrequencyNumber = f.getNumber()+" "+f.getUnit();
    					medicationDetails.put("frequency", medicationFrequencyNumber);
    				}
    			}
        	}

        	if (neAnnot.getMedicationDuration() != null) {
        		MedicationDurationModifier durationModifier = neAnnot.getMedicationDuration();
    			if (durationModifier != null) {
    				MedicationDuration d = (MedicationDuration) durationModifier.getNormalizedForm();
    				if (d!=null) {
    					String duration = d.getValue();
    					medicationDetails.put("duration", duration);
    				}
    			}
        	}
			
        	if (neAnnot.getMedicationRoute() != null) {
        		MedicationRouteModifier routeModifier = neAnnot.getMedicationRoute();
    			if (routeModifier != null) {
    				MedicationRoute r = (MedicationRoute) routeModifier.getNormalizedForm();
    				if (r != null) {
    					String route = r.getValue();
    					medicationDetails.put("route", route);
    				}
    			}
        	}			

        	if (neAnnot.getMedicationForm() != null) {
        		MedicationFormModifier formModifier = neAnnot.getMedicationForm();
    			if (formModifier != null) {
    				MedicationForm f = (MedicationForm) formModifier.getNormalizedForm();
    				if (f!=null) {
    					String form = f.getValue();
    					medicationDetails.put("form", form);
    				}
    			}
        	}
			
        	if (neAnnot.getMedicationStatusChange() != null) {
        		MedicationStatusChangeModifier scModifier = neAnnot.getMedicationStatusChange();
    			if (scModifier != null) {
    				MedicationStatusChange sc = (MedicationStatusChange) scModifier.getNormalizedForm();
    				if (sc!=null) {
    					String changeStatus = sc.getValue();
    					medicationDetails.put("changeStatus", changeStatus);
    				}
    			}
        	}
        	
        	if (neAnnot.getStartDate() != null) {
        		TimeMention startDate = neAnnot.getStartDate();    			
				String stDate = startDate.getDate().toString();
				medicationDetails.put("startDate", stDate);

        	}
        	
        	if (neAnnot.getEndDate() != null) {
        		TimeMention endDate = neAnnot.getEndDate();    			
				String edDate = endDate.getDate().toString();
				medicationDetails.put("endDate", edDate);

        	}
			
        	if (!medicationDetails.isEmpty()) {
        		medicationDetailsList.add(medicationDetails);
        	}

        }
        
        

        if(annotation instanceof IdentifiedAnnotation) {
            IdentifiedAnnotation ia = (IdentifiedAnnotation) annotation;
            confidence = ia.getConfidence();
            polarity = ia.getPolarity();
            uncertainty = ia.getUncertainty();
            historyOf = ia.getHistoryOf();
            subject = ia.getSubject();
            
            if(ia.getOntologyConceptArr() != null) {
                for (UmlsConcept concept : JCasUtil.select(ia.getOntologyConceptArr(), UmlsConcept.class)) {
                    Map<String, Object> atts = new HashMap<>();
                    atts.put("codingScheme", concept.getCodingScheme());
                    atts.put("cui", concept.getCui());
                    atts.put("code", concept.getCode());
                    atts.put("tui", concept.getTui());
                    atts.put("preferredText", concept.getPreferredText());
                    
                    if (anatomyAnnotation) {
                    	atts.put("bodyRegion", "");
                    }
                    
                    conceptAttributes.add(atts);
                }
            }
            
            relations = JCasUtil.select(jcas, BinaryTextRelation.class).stream()
            		.map( r -> {
						try {
							return getRelationText( ia, r );
						} catch (SQLException e) {
							// TODO Auto-generated catch block
							e.printStackTrace();
							return null;
						}
						
					} )
            		.filter(result -> result != null && !result.isEmpty())
            		.distinct()
            		.collect( Collectors.toList() );
            
//            if (text.equals("labial tear")) {
//            	System.out.println("test");
//            }
            
            // we got more than 1 relations so check to see if one relation contains the other(s) or not
            // only keep the broader option: 
            // Relation 1: Right Shoulder
            // Relation 2: Shoulder
            // Keep Relation 1 only
            
            List<Map<String, Object>> temp_rels = new ArrayList<>() ;
            
            try {
            	if (relations.size() > 1 ) {
                	for (int i = 0; i < relations.size(); i++) {
                    	// take first relation and loop through all relations again
                    	Map<String, Object> r = relations.get(i);
                    	
                    	for (Map<String, Object> r1 : relations) {
                    		// dont compare the same relation:
                    		if (r1.get("text") != r.get("text")) {
//                    			System.out.println(r.get("begin"));
//                    			System.out.println(r1.get("begin"));
//                    			System.out.println(r.get("end"));
//                    			System.out.println(r1.get("end"));
//                    			System.out.println(r.get("text"));
//                    			System.out.println(r1.get("text"));
                    			if (((Integer) r.get("begin")).intValue() >= ((Integer) r1.get("begin")).intValue() 
                    					&& ((Integer) r.get("end")).intValue() <= ((Integer) r1.get("end")).intValue()) {
                    				temp_rels.add(r);
                    			} 
                    		}
                    	}
                    }
                }
                relations.removeAll(temp_rels);
            } catch (Exception e) {
            	e.printStackTrace();
			}
            
        }
    }

    final public String getType() {
        return _type;
    }
    
    private Map<String, Object> getRelationText( final IdentifiedAnnotation annotation, final BinaryTextRelation relation ) throws SQLException {
    	Map<String, Object> atts = new HashMap<>();
    	List<Map<String,Object>> local_conceptAttributes = new ArrayList<>();
    	
		if ( relation.getArg1().getArgument().equals( annotation ) ) {
			
			String arg2SafeText = getSafeText( relation.getArg2().getArgument() );
			
			// only add argument 2 if it is different from annotation
			if (!Integer.valueOf(relation.getArg2().getArgument().getBegin()).equals(Integer.valueOf(annotation.getBegin())) && 
					!Integer.valueOf(relation.getArg2().getArgument().getEnd()).equals(Integer.valueOf(annotation.getEnd())) &&
					!arg2SafeText.equals( getSafeText( relation.getArg1().getArgument() ))) {
//				atts.put("Arg1IsAnnotation", true);
				atts.put("Relation_Category", relation.getCategory());
				atts.put("text", arg2SafeText);
				atts.put("begin", relation.getArg2().getArgument().getBegin());
				atts.put("end", relation.getArg2().getArgument().getEnd() );
				atts.put("arg2Type", relation.getArg2().getArgument().getClass().getSimpleName());
				
				FSArray onto = ((IdentifiedAnnotation) relation.getArg2().getArgument()).getOntologyConceptArr();
				
				if(onto != null) {
	                for (UmlsConcept concept : JCasUtil.select(onto, UmlsConcept.class)) {
	                    Map<String, Object> annotation_onto_concepts = new HashMap<>();
	                    annotation_onto_concepts.put("codingScheme", concept.getCodingScheme());
	                    annotation_onto_concepts.put("cui", concept.getCui());
	                    annotation_onto_concepts.put("code", concept.getCode());
	                    annotation_onto_concepts.put("tui", concept.getTui());
	                    annotation_onto_concepts.put("preferredText", concept.getPreferredText());
	                    
	                    if (relation.getArg2().getArgument() instanceof AnatomicalSiteMention) {
	                    	annotation_onto_concepts.put("bodyRegion", "");
	                    }
	                    local_conceptAttributes.add(annotation_onto_concepts);
	                }
	            }
				atts.put("rel_concept", local_conceptAttributes);
			}
			return atts;			
		
		} else if ( relation.getArg2().getArgument().equals( annotation ) ) {
			
			String arg1SafeText = getSafeText( relation.getArg1().getArgument() );
			
			// only add argument 1 if it is different from annotation
			if (!Integer.valueOf(relation.getArg1().getArgument().getBegin()).equals(Integer.valueOf(annotation.getBegin())) && 
					!Integer.valueOf(relation.getArg1().getArgument().getEnd()).equals(Integer.valueOf(annotation.getEnd())) &&
					!arg1SafeText.equals( getSafeText( relation.getArg2().getArgument() ))) {
			
//				atts.put("Arg2IsAnnotation", true);
				atts.put("Relation_Category", relation.getCategory());
				
				atts.put("text", getSafeText( relation.getArg1().getArgument() ));
				atts.put("begin", relation.getArg1().getArgument().getBegin());
				atts.put("end", relation.getArg1().getArgument().getEnd() );
				atts.put("arg1Type", relation.getArg1().getArgument().getClass().getSimpleName());
				
	//			atts.put("Argument2Text", getSafeText( relation.getArg2().getArgument() ));
	//			atts.put("Argument2TextBegin", relation.getArg2().getArgument().getBegin());
	//			atts.put("Argument2TextEnd", relation.getArg2().getArgument().getEnd() );
	//			atts.put("Arg2Role", relation.getArg2().getRole());
				
				FSArray onto = ((IdentifiedAnnotation) relation.getArg1().getArgument()).getOntologyConceptArr();
				
				if(onto != null) {
	                for (UmlsConcept concept : JCasUtil.select(onto, UmlsConcept.class)) {
	                    Map<String, Object> annotation_onto_concepts = new HashMap<>();
	                    annotation_onto_concepts.put("codingScheme", concept.getCodingScheme());
	                    annotation_onto_concepts.put("cui", concept.getCui());
	                    annotation_onto_concepts.put("code", concept.getCode());
	                    annotation_onto_concepts.put("tui", concept.getTui());
	                    annotation_onto_concepts.put("preferredText", concept.getPreferredText());
	                    
	                    if (relation.getArg1().getArgument() instanceof AnatomicalSiteMention) {
	                    	annotation_onto_concepts.put("bodyRegion", "");
	                    }
	                    
	                    local_conceptAttributes.add(annotation_onto_concepts);
	                }
	            }
				atts.put("rel_concept", local_conceptAttributes);
			}
			return atts;
//			return getSafeText( relation.getArg1().getArgument() ) + " [" + relation.getCategory() + "]";
		}
		
		return null;
	}
    
    static private String getSafeText( final Annotation annotation ) {
        if ( annotation == null ) {
           return "";
        }
        return getSafeText( annotation.getCoveredText().trim() );
     }
    
    static private String getSafeText( final String text ) {
        if ( text == null || text.isEmpty() ) {
           return "";
        }
        String safeText = text.replaceAll( "'", "&apos;" );
        safeText = safeText.replaceAll( "\"", "&quot;" );
        safeText = safeText.replaceAll( "@", "&amp;" );
        safeText = safeText.replaceAll( "<", "&lt;" );
        safeText = safeText.replaceAll( ">", "&gt;" );
        return safeText;
     }

}
