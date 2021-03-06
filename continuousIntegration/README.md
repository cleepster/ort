# How to run
### Requirements 

Installed:
- docker
- docker-compose
 
### First run  
Run in directory continuousIntegration
```
docker-compose up
```
It creates and starts containers:
- Jenkins   -> localhost:8080
- Sonar     -> localhost:9000 

To stop containers use:
```
docker-compose stop
```

To remove containers from disk space use: (server data will be lost) 
```
docker-compose down 
``` 
### Next runs
Start containers
```
docker-compose start
```
Stop containers
```
docker-compose stop
```
Restart containers 
```
docker-compose restart
```
List running containers 
```
docker ps
```

# Extra information
## Jenkins  
### Plugins
jenkins/plugins.txt contains list plugins which will be installed on first jenkins server run

* git - support git  
* python - support manage python 
* pyenv - support virtual environment 
* sonar - support sonar scanner, enable code analysis 
* configuration-as-code - enable configuration all plugins by .yml file 
* test-results-analyzer - generate test reports on jenkins jobs


### Using Code as config plugin 
https://github.com/jenkinsci/configuration-as-code-plugin
### Jobs description   
* integration - runs integration tests
* unittest - runs unit tests
* sonar_master - on branch 'master' calculate code coverage, run sonar scanner and push results to sonar server 
* sonar_stable - on branch 'stable' calculate code coverage, run sonar scanner and push results to sonar server 

### Adding new job to repository 
1 Create Job in jenkins <br>
2 Go to Job endpoint with xml extension e.g.:
```
http://localhost:8080/job/unittest/config.xml
```
3 Copy above config.xml file to 
```
jenkins/jobs/new_job_titel/config.xml
```
## Sonar 
### Sonar parameters on jenkins job stage with examples
Project Key - name of project on sonar server 
```
sonar.projectKey=aamks-master
```
Exclude path . Paths will be exclude from analysis
```
sonar.exclusions=dev/**
```
Coverage report path - path to coverage report which will be send to sonar server  
```
sonar.python.coverage.reportPaths=coverage.xml
```