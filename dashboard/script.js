// =========================================================
// DEPLOYGUARD NEXUS DASHBOARD
// =========================================================


// =========================================================
// LOAD DASHBOARD
// =========================================================

async function loadDashboard() {

    try {

        const response = await fetch(
            "/api/deployments"
        );


        if (!response.ok) {

            throw new Error(
                "Unable to load deployment data."
            );

        }


        const data =
            await response.json();


        // =================================================
        // SUMMARY
        // =================================================

        const summary =
            data.summary || {};


        document.getElementById(
            "riskScore"
        ).textContent =
            summary.riskScore ?? "--";


        document.getElementById(
            "riskLevel"
        ).textContent =
            summary.riskLevel || "--";


        document.getElementById(
            "decision"
        ).textContent =
            summary.decision || "--";


        // =================================================
        // DEPLOYMENTS
        // =================================================

        const deployments =
            Array.isArray(data.deployments)
                ? data.deployments
                : [];


        // =================================================
        // LATEST DEPLOYMENT
        // =================================================

        const latest =
            deployments.length > 0
                ? deployments[0]
                : null;


        // =================================================
        // FIND LATEST DEPLOYMENT WITH RISK ANALYSIS
        // =================================================

        const analysisDeployment =
            deployments.find(
                deployment =>
                    deployment.testFailures !== undefined ||
                    deployment.coverage !== undefined ||
                    deployment.changedFiles !== undefined ||
                    deployment.securityIssues !== undefined ||
                    deployment.testsPassed !== undefined ||
                    deployment.previousFailures !== undefined ||
                    deployment.metrics !== undefined
            ) || latest;


        // =================================================
        // LATEST DEPLOYMENT DISPLAY
        // =================================================

        if (latest) {

            document.getElementById(
                "latestId"
            ).textContent =
                latest.id || "--";


            document.getElementById(
                "latestRisk"
            ).textContent =
                latest.riskScore ?? "--";


            document.getElementById(
                "latestLevel"
            ).textContent =
                latest.riskLevel || "--";


            document.getElementById(
                "latestDecision"
            ).textContent =
                latest.decision || "--";


            document.getElementById(
                "latestStatus"
            ).textContent =
                latest.status || "--";

        }


        // =================================================
        // RISK ANALYSIS
        // =================================================

        if (analysisDeployment) {

            /*
             * Some older deployments store metrics directly:
             *
             * testFailures
             * coverage
             * changedFiles
             * securityIssues
             * testsPassed
             * previousFailures
             *
             * Some deployments may store them inside:
             *
             * metrics: {
             *     testFailures: ...,
             *     coverage: ...,
             *     changedFiles: ...,
             *     securityIssues: ...,
             *     testsPassed: ...,
             *     previousFailures: ...
             * }
             */


            const metrics =
                analysisDeployment.metrics || {};


            const testFailures =
                analysisDeployment.testFailures ??
                metrics.testFailures;


            const coverage =
                analysisDeployment.coverage ??
                metrics.coverage;


            const changedFiles =
                analysisDeployment.changedFiles ??
                metrics.changedFiles;


            const previousFailures =
                analysisDeployment.previousFailures ??
                metrics.previousFailures;


            const securityIssues =
                analysisDeployment.securityIssues ??
                metrics.securityIssues;


            const testsPassed =
                analysisDeployment.testsPassed ??
                metrics.testsPassed;


            // =================================================
            // TEST FAILURES
            // =================================================

            document.getElementById(
                "testFailures"
            ).textContent =
                testFailures ?? "--";


            // =================================================
            // COVERAGE
            // =================================================

            document.getElementById(
                "coverage"
            ).textContent =
                coverage !== undefined &&
                coverage !== null
                    ? `${Number(coverage).toFixed(1)}%`
                    : "--";


            // =================================================
            // CHANGED FILES
            // =================================================

            document.getElementById(
                "changedFiles"
            ).textContent =
                changedFiles ?? "--";


            // =================================================
            // PREVIOUS FAILURES
            // =================================================

            document.getElementById(
                "previousFailures"
            ).textContent =
                previousFailures ?? "--";


            // =================================================
            // SECURITY ISSUES
            // =================================================

            document.getElementById(
                "securityIssues"
            ).textContent =
                securityIssues ?? "--";


            // =================================================
            // TESTS PASSED
            // =================================================

            document.getElementById(
                "testsPassed"
            ).textContent =
                testsPassed ?? "--";

        }


        // =================================================
        // NO DEPLOYMENTS
        // =================================================

        else {

            document.getElementById(
                "latestId"
            ).textContent = "--";


            document.getElementById(
                "latestRisk"
            ).textContent = "--";


            document.getElementById(
                "latestLevel"
            ).textContent = "--";


            document.getElementById(
                "latestDecision"
            ).textContent = "--";


            document.getElementById(
                "latestStatus"
            ).textContent = "--";


            document.getElementById(
                "testFailures"
            ).textContent = "--";


            document.getElementById(
                "coverage"
            ).textContent = "--";


            document.getElementById(
                "changedFiles"
            ).textContent = "--";


            document.getElementById(
                "previousFailures"
            ).textContent = "--";


            document.getElementById(
                "securityIssues"
            ).textContent = "--";


            document.getElementById(
                "testsPassed"
            ).textContent = "--";

        }


        // =================================================
        // DEPLOYMENT HISTORY
        // =================================================

        const table =
            document.getElementById(
                "deploymentTable"
            );


        table.innerHTML = "";


        deployments.forEach(
            deployment => {


                const row =
                    document.createElement(
                        "tr"
                    );


                row.innerHTML = `

                    <td>
                        ${deployment.id || "--"}
                    </td>

                    <td>
                        ${deployment.riskScore ?? "--"}
                    </td>

                    <td>
                        ${deployment.riskLevel || "--"}
                    </td>

                    <td>
                        ${deployment.decision || "--"}
                    </td>

                    <td>
                        ${deployment.status || "--"}
                    </td>

                    <td>
                        ${
                            deployment.rollback
                                ? "Yes"
                                : "No"
                        }
                    </td>

                `;


                table.appendChild(
                    row
                );

            }
        );


    }


    catch (error) {

        console.error(
            "Dashboard error:",
            error
        );


        document.getElementById(
            "riskLevel"
        ).textContent =
            "ERROR";


        document.getElementById(
            "decision"
        ).textContent =
            "DATA UNAVAILABLE";


        document.getElementById(
            "testFailures"
        ).textContent =
            "--";


        document.getElementById(
            "coverage"
        ).textContent =
            "--";


        document.getElementById(
            "changedFiles"
        ).textContent =
            "--";


        document.getElementById(
            "previousFailures"
        ).textContent =
            "--";


        document.getElementById(
            "securityIssues"
        ).textContent =
            "--";


        document.getElementById(
            "testsPassed"
        ).textContent =
            "--";

    }

}



// =========================================================
// REAL PROJECT ANALYZER
// =========================================================

async function analyzeProject() {

    const repositoryInput =
        document.getElementById(
            "repositoryUrl"
        );


    const resultBox =
        document.getElementById(
            "analysisResult"
        );


    const button =
        document.getElementById(
            "analyzeButton"
        );


    const repository =
        repositoryInput.value.trim();


    // =====================================================
    // VALIDATE INPUT
    // =====================================================

    if (!repository) {

        resultBox.innerHTML = `

            <h3>
                Repository Required
            </h3>

            <p>
                Please enter a GitHub repository URL.
            </p>

        `;


        resultBox.style.display =
            "block";


        return;

    }


    // =====================================================
    // START ANALYSIS
    // =====================================================

    button.disabled = true;


    button.textContent =
        "Analyzing...";


    resultBox.style.display =
        "block";


    resultBox.innerHTML = `

        <h3>
            Analyzing Project...
        </h3>

        <p>
            Cloning repository,
            installing dependencies,
            running tests,
            calculating coverage
            and scanning for security issues...
        </p>

    `;


    try {

        // =================================================
        // CALL BACKEND
        // =================================================

        const response =
            await fetch(
                "/api/analyze",
                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body:
                        JSON.stringify({

                            repository:
                                repository

                        })

                }
            );


        const result =
            await response.json();


        // =================================================
        // CHECK RESPONSE
        // =================================================

        if (
            !response.ok ||
            !result.success
        ) {

            throw new Error(

                result.error ||
                "Project analysis failed."

            );

        }


        // =================================================
        // DISPLAY ANALYSIS
        // =================================================

        resultBox.innerHTML = `

            <h3>
                Deployment Analysis
            </h3>


            <p>

                <strong>
                    Project:
                </strong>

                ${result.repository}

            </p>


            <div class="analysis-result-grid">


                <div>

                    <span>
                        Tests Passed
                    </span>

                    <strong>
                        ${result.tests_passed}
                    </strong>

                </div>


                <div>

                    <span>
                        Test Failures
                    </span>

                    <strong>
                        ${result.test_failures}
                    </strong>

                </div>


                <div>

                    <span>
                        Code Coverage
                    </span>

                    <strong>
                        ${result.coverage}%
                    </strong>

                </div>


                <div>

                    <span>
                        Security Issues
                    </span>

                    <strong>
                        ${result.security_issues}
                    </strong>

                </div>


                <div>

                    <span>
                        Changed Files
                    </span>

                    <strong>
                        ${result.changed_files}
                    </strong>

                </div>


                <div>

                    <span>
                        Previous Failures
                    </span>

                    <strong>
                        ${result.previous_failures}
                    </strong>

                </div>


            </div>


            <hr>


            <div class="deployment-decision">


                <h3>
                    Deployment Decision
                </h3>


                <div class="decision-grid">


                    <div>

                        <span>
                            Risk Score
                        </span>

                        <strong>
                            ${result.risk_score}
                        </strong>

                    </div>


                    <div>

                        <span>
                            Risk Level
                        </span>

                        <strong>
                            ${result.risk_level}
                        </strong>

                    </div>


                    <div>

                        <span>
                            Decision
                        </span>

                        <strong>
                            ${result.decision}
                        </strong>

                    </div>


                </div>


            </div>


            <p>

                Analysis ID:

                <strong>
                    ${result.deployment_id}
                </strong>

            </p>


            <p>

                <strong>

                    ${
                        result.decision ===
                        "APPROVED"

                            ? "Deployment approved. Risk level is within the safe threshold."

                            : result.decision ===
                              "VALIDATION_REQUIRED"

                            ? "Deployment requires additional validation before release."

                            : "Deployment blocked because the calculated risk is too high."
                    }

                </strong>

            </p>

        `;


        // =================================================
        // REFRESH DASHBOARD
        // =================================================

        await loadDashboard();


    }


    catch (error) {

        console.error(
            "Analysis error:",
            error
        );


        resultBox.innerHTML = `

            <h3>
                Analysis Failed
            </h3>

            <p>
                ${error.message}
            </p>

        `;

    }


    finally {

        button.disabled = false;


        button.textContent =
            "Analyze Project";

    }

}



// =========================================================
// INITIAL DASHBOARD LOAD
// =========================================================

loadDashboard();