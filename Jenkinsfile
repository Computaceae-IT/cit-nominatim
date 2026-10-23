// Preparation pipeline: deliberately no Docker build, push, SSH or deployment.
// DB builds remain blocked until persistence and a restore drill are reviewed.
node {
    properties([buildDiscarder(logRotator(numToKeepStr: '5'))])
    stage('Checkout') { checkout scm }
    // stage('Validate preparation') {
    //     sh 'python3 -m unittest discover -s tests -v'
    //     sh 'for script in API/verify-php.sh API/startapache.sh DB/verify-php.sh DB/startpostgres.sh scripts/inspect-db.sh; do sh -n "$script"; done'
    //     sh 'git diff --check'
    // }
    stage('Manual release required') {
        echo 'See docs/security-2026-10-23.md. No build, publish or deploy is automatic.'
    }
}
