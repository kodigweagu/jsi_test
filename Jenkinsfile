pipeline {
  agent any

  triggers {
    githubPush()
  }

  environment {
    IMAGE_NAME = "myapp"
    AWS_REGION = "us-east-1"
    ECR_ACCOUNT_ID = "123456789012"
    ECR_REPO = "${ECR_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${IMAGE_NAME}"
    SONAR_HOST_URL = "https://sonar.example.com"
    SNYK_TOKEN = credentials("snyk-token")
    ALERTMANAGER_URL = "https://alertmanager.example.com"
  }

  stages {
    stage("Checkout") {
      steps {
        checkout([$class: "GitSCM",
          branches: [[name: "*/main"]],
          userRemoteConfigs: [[url: "https://github.com/<org>/<repo>.git"]]
        ])
      }
    }

    stage("Install Dependencies") {
      steps {
        sh "pip install -r requirements.txt"
      }
    }

    stage("Lint") {
      steps {
        sh "pylint app tests"
      }
    }

    stage("Tests + Coverage") {
      steps {
        sh "pytest --cov --cov-report=term-missing --cov-fail-under=100 --ignore=tests/smoke"
      }
    }

    stage("Build Image") {
      steps {
        script {
          def version = sh(script: "gitversion /showvariable SemVer", returnStdout: true).trim()
          env.IMAGE_TAG = version
          sh "docker build -t ${IMAGE_NAME}:${IMAGE_TAG} ."
        }
      }
    }

    stage("Vulnerability Scans") {
      steps {
        sh """
          trivy image --exit-code 1 --severity HIGH,CRITICAL ${IMAGE_NAME}:${IMAGE_TAG}
          snyk auth ${SNYK_TOKEN}
          snyk test --severity-threshold=high
          snyk container test ${IMAGE_NAME}:${IMAGE_TAG} --severity-threshold=high
          checkov -d . --quiet --compact --soft-fail=false
        """
        withSonarQubeEnv("sonarqube") {
          sh """
            sonar-scanner \
              -Dsonar.projectKey=myapp \
              -Dsonar.sources=app \
              -Dsonar.host.url=${SONAR_HOST_URL}
          """
        }
        sh """
          dependency-check \
            --project myapp \
            --scan . \
            --format HTML \
            --out dependency-check-report \
            --failOnCVSS 7
        """
      }
    }

    stage("Push Image") {
      steps {
        withCredentials([[$class: "AmazonWebServicesCredentialsBinding", credentialsId: "aws-creds"]]) {
          sh """
            aws ecr get-login-password --region ${AWS_REGION} | \
              docker login --username AWS --password-stdin ${ECR_REPO}
            docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${ECR_REPO}:${IMAGE_TAG}
            docker push ${ECR_REPO}:${IMAGE_TAG}
          """
        }
      }
    }

    stage("Deploy to Staging") {
      steps {
        withKubeConfig([credentialsId: "kubeconfig-staging"]) {
          sh """
            helm upgrade --install myapp ./helm \
              --namespace staging --create-namespace \
              --set image.repository=${ECR_REPO} \
              --set image.tag=${IMAGE_TAG}
          """
        }
      }
    }

    stage("Smoke Tests (Staging)") {
      steps {
        script {
          def baseUrl = "https://staging.example.com"
          sh """
            curl -fsS ${baseUrl}/health
            curl -fsS ${baseUrl}/ready
            BASE_URL=${baseUrl} pytest -q tests/smoke
          """
        }
      }
    }

    stage("Deploy Canary (Production)") {
      steps {
        withKubeConfig([credentialsId: "kubeconfig-prod"]) {
          sh """
            helm upgrade --install myapp ./helm \
              --namespace prod --create-namespace \
              --set image.repository=${ECR_REPO} \
              --set image.tag=${IMAGE_TAG} \
              --set canary.enabled=true \
              --set canary.weight=5
          """
        }
      }
    }

    stage("Monitor Canary Alerts") {
      steps {
        script {
          def attempts = 6
          def sleepMinutes = 5
          for (int i = 0; i < attempts; i++) {
            def alerts = sh(
              script: "curl -fsS ${ALERTMANAGER_URL}/api/v2/alerts?active=true",
              returnStdout: true
            ).trim()
            if (alerts && alerts != "[]") {
              echo "Active alerts detected, rolling back."
              sh """
                PREV_REV=\$(helm history myapp --namespace prod | tail -n 2 | head -n 1 | awk '{print \$1}')
                if [ -n \"\${PREV_REV}\" ]; then
                  helm rollback myapp \${PREV_REV} --namespace prod || true
                fi
                helm upgrade myapp ./helm --namespace prod --set canary.enabled=false
              """
              error("Rollback triggered due to alerts")
            }
            sleep(time: sleepMinutes, unit: "MINUTES")
          }
        }
      }
    }
  }

  post {
    failure {
      echo "Pipeline failed. Investigate logs and consider rollback."
    }
  }
}

// Canary weight updates should run in a separate cron-triggered job.
// That job reads the rollout start time and applies:
//   helm upgrade myapp ./helm --namespace prod --set canary.weight=<computed>
// The job can run every 6 hours and map elapsed time to weights (5/25/50/75/100).
