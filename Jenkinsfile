node {

  	properties([
    	buildDiscarder(logRotator(numToKeepStr:'5'))
  	])

    /* define variable */
    def app

	try {

		stage('Clone repository') {
			/* Let's make sure we have the repository cloned to our workspace */
			checkout scm
		}

		stage('SED Deployment variable') {
			script {
				env.DEPLOY_COMMIT_HASH = sh(returnStdout: true, script: "git rev-parse HEAD | cut -c1-7").trim()
				env.DEPLOY_BUILD_DATE = sh(returnStdout: true, script: "date -u +'%Y-%m-%dT%H.%M.%SZ'").trim()
			}
		}

		stage('Build and Push image') {
			app = docker.build("registry.computaceae-it.tech/cit-nominatim:${env.DEPLOY_COMMIT_HASH}");
			app.push()
		}

		switch (env.BRANCH_NAME) {
			case "master":
			case "main":
				stage('Tag image PRD') {
					app.push("latest")
				}
				break;
		}

	}catch (InterruptedException err) {
		// nothing
	}catch (Exception err) {
		mail (to: 'cyril.boillat@ville-ge.ch',
		subject: "[ ERROR ] Job '${env.JOB_NAME}' (${env.BUILD_NUMBER}) is build error",
		body: "Please go to ${env.JOB_URL}.\nPlease go to console ${env.BUILD_URL}console.\n\n${err}");
		throw err
	}

}