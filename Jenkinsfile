pipeline {
    agent { label 'windows' }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup') {
            steps {
                bat 'python -m venv .venv'
                bat '.venv\\Scripts\\pip install --upgrade pip'
                bat '.venv\\Scripts\\pip install -r requirements.txt -r requirements-dev.txt pyinstaller'
            }
        }

        stage('Test') {
            steps {
                bat '.venv\\Scripts\\python -m pytest tests/ -m "not (integration or ollama or web or windows_only or e2e or gui or cli or full_flow)" -v'
            }
        }

        stage('Build') {
            steps {
                bat '.venv\\Scripts\\pyinstaller --onefile --name Apps-Analyst main.py'
            }
        }
    }

    post {
        success {
            archiveArtifacts artifacts: 'dist/*.exe', fingerprint: true
        }
        always {
            cleanWs()
        }
    }
}
