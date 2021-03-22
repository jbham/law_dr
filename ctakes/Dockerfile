FROM openjdk:8-alpine
# FROM adoptopenjdk/openjdk11:alpine

RUN apk update && apk add ca-certificates openssl wget unzip subversion maven

## Download apache-tomcat and extract:
RUN wget http://mirror.cogentco.com/pub/apache/tomcat/tomcat-9/v9.0.44/bin/apache-tomcat-9.0.44.zip
RUN unzip apache-tomcat-9.0.44.zip

## Check out version of ctakes with best working web-rest module
## Then compile with maven
# checked out 1876524 on April 14th, 2020
RUN svn co https://svn.apache.org/repos/asf/ctakes/trunk@1876524

# move custom changes to changes from CTAKES
COPY ctakes_custom_changes/ trunk/

## copy dictionary 
COPY customDictionary.xml /trunk/ctakes-web-rest/src/main/resources/org/apache/ctakes/dictionary/lookup/fast/
COPY pom.xml /trunk
COPY rest_pom.xml /trunk/ctakes-web-rest/pom.xml

# WORKDIR /ctakes
RUN mvn compile -DskipTests
# updated commands to skip unnecessary stuff:
# mvn compile -pl '!ctakes-distribution' -pl '!ctakes-ytex' -pl '!ctakes-ytex-uima' -pl '!ctakes-ytex-web'  -DskipTests

RUN mvn install -pl '!ctakes-distribution'  -DskipTests
# mvn install -pl '!ctakes-distribution' -pl '!ctakes-ytex' -pl '!ctakes-ytex-uima' -pl '!ctakes-ytex-web' -DskipTests


WORKDIR /
# RUN cp /ctakes/ctakes-web-rest/target/ctakes-web-rest.war /apache-tomcat-9.0.34/webapps/
COPY ./trunk/ctakes-web-rest/target/ctakes-web-rest.war /apache-tomcat-9.0.44/webapps/

ENV TOMCAT_HOME=/apache-tomcat-9.0.44
# ENV CTAKES_HOME=/ctakes

EXPOSE 8080


WORKDIR $TOMCAT_HOME
RUN chmod u+x bin/*.sh
RUN touch bin/setenv.sh
RUN echo "export CATALINA_OPTS=\"$CATALINA_OPTS -Xms5120m -Xmx5120m\"" >> bin/setenv.sh

CMD bin/catalina.sh run
