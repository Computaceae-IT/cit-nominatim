node {

  	properties([
    	buildDiscarder(logRotator(numToKeepStr:'5'))
  	])

    /* define variable */
    def api
	def ui

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

			dir ('k8s') {
				sh "sed -i \"s|DATE_DEPLOYMENT|${env.DEPLOY_BUILD_DATE}|g\" 004.deployment.API.yaml"
				sh "sed -i \"s|DATE_DEPLOYMENT|${env.DEPLOY_BUILD_DATE}|g\" 004.deployment.UI.yaml"
			}
		}

		stage('Build and Push image API') {
			dir ('API') {
				api = docker.build("registry.computaceae-it.tech/cit-nominatim-api:${env.DEPLOY_COMMIT_HASH}");
				api.push()
			}
		}

		stage('Build and Push image UI') {
			dir ('UI') {
				ui = docker.build("registry.computaceae-it.tech/cit-nominatim-ui:${env.DEPLOY_COMMIT_HASH}");
				ui.push()
			}
		}

		switch (env.BRANCH_NAME) {
			case "master":
			case "main":
				stage('Tag image PRD') {
					api.push("latest")
					ui.push("latest")
				}

				stage('Apply Kubernetes files') {
					withKubeConfig([credentialsId: 'cit-kube-config']) {
						dir ('k8s') {
							sh 'kubectl apply -f 003.service.API.yaml'
							sh 'kubectl apply -f 004.deployment.API.yaml'
							sh 'kubectl apply -f 003.service.UI.yaml'
							sh 'kubectl apply -f 004.deployment.UI.yaml'
						}
					}
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