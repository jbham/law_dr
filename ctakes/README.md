CTAKES

Required pre-configuration information

- Obtain UMLS credentials

Setup:

- Update UMLS credentials in
  ctakes-web-rest/resource/org/apache/ctakes/dictionary/lookup/fast/customDictionary.xml on line 42, 44, 63 and 65
  ctakes-web-rest/resource/org/apache/ctakes/pipers/default/TsDictionarySubPipe.piper
  ctakes-web-rest/resource/org/apache/ctakes/pipers/TsDictionarySubPipe.piper

- Update mysql, postgres or HSQLDB entry class:
  ctakes-web-rest/resource/org/apache/ctakes/dictionary/lookup/fast/customDictionary.xml on line 31 and 53

- Update mysql, postgres or HSQLDB JDBC url:
  ctakes-web-rest/resource/org/apache/ctakes/dictionary/lookup/fast/customDictionary.xml on line 42, 44, 63 and 65

Run:

- Start docker container using DockerFile
