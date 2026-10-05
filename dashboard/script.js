// =========================================================
// DEPLOYGUARD NEXUS
// Dashboard + Deployment Risk Demo
// =========================================================


// =========================================================
// LOAD DASHBOARD
// =========================================================

async function loadDashboard() {

    try {

        const response =
            await fetch("/api/deployments");

        if (!response.ok) {
            throw new Error(
                "Unable to load deployment data."
            );
        }

        const data =
            await response.json();


        // -------------------------------------------------
        // SUMMARY
        // -------------------------------------------------

        document.getElementById(
            "riskScore"
        ).textContent =
            data.summary.riskScore ?? "--";


        document.getElementById(
            "riskLevel"
        ).textContent =
            data.summary.riskLevel ?? "--";


        document.getElementById(
            "decision"
        ).textContent =
            data.summary.decision ?? "--";


        // -------------------------------------------------
        // LATEST DEPLOYMENT
        // -------------------------------------------------

        const latest =
            data.deployments &&
            data.deployments.length > 0
                ? data.deployments[0]
                : null;


        if (latest) {

            document.getElementById(
                "latestId"
            ).textContent =
                latest.id ?? "--";


            document.getElementById(
                "latestRisk"
            ).textContent =
                latest.riskScore ?? "--";


            document.getElementById(
                "latestLevel"
            ).textContent =
                latest.riskLevel ?? "--";


            document.getElementById(
                "latestDecision"
            ).textContent =
                latest.decision ?? "--";


            document.getElementById(
                "latestStatus"
            ).textContent =
                latest.status ?? "--";


            // -------------------------------------------------
            // RISK METRICS
            // -------------------------------------------------

            const metrics =
                latest.metrics || {};


            document.getElementById(
                "testFailures"
            ).textContent =
                metrics.testFailures ?? "--";


            document.getElementById(
                "coverage"
            ).textContent =
                metrics.coverage !== undefined
                    ? Number(
                        metrics.coverage
                    ).toFixed(1) + "%"
                    : "--";


            document.getElementById(
                "securityIssues"
            ).textContent =
                metrics.securityIssues ?? "--";


            document.getElementById(
                "changedFiles"
            ).textContent =
                metrics.changedFiles ?? "--";


            document.getElementById(
                "previousFailures"
            ).textContent =
                metrics.previousFailures ?? "--";
        }


        // -------------------------------------------------
        // DEPLOYMENT HISTORY
        // -------------------------------------------------

        const table =
            document.getElementById(
                "deploymentTable"
            );


        table.innerHTML = "";


        if (
            !data.deployments ||
            data.deployments.length === 0
        ) {

            const row =
                document.createElement("tr");


            row.innerHTML = `
                <td colspan="6">
                    No deployments found.
                </td>
            `;


            table.appendChild(row);

            return;
        }


        data.deployments.forEach(
            deployment => {

                const row =
                    document.createElement("tr");


                row.innerHTML = `

                    <td>
                        ${escapeHtml(
                            deployment.id ?? "--"
                        )}
                    </td>

                    <td>
                        ${deployment.riskScore ?? "--"}
                    </td>

                    <td>
                        ${escapeHtml(
                            deployment.riskLevel ?? "--"
                        )}
                    </td>

                    <td>
                        ${escapeHtml(
                            deployment.decision ?? "--"
                        )}
                    </td>

                    <td>
                        ${escapeHtml(
                            deployment.status ?? "--"
                        )}
                    </td>

                    <td>
                        ${
                            deployment.rollback
                                ? "Yes"
                                : "No"
                        }
                    </td>

                `;


                table.appendChild(row);
            }
        );


    } catch (error) {

        console.error(
            "Dashboard error:",
            error
        );


        document.getElementById(
            "riskScore"
        ).textContent = "ERROR";


        document.getElementById(
            "riskLevel"
        ).textContent = "ERROR";


        document.getElementById(
            "decision"
        ).textContent =
            "DATA UNAVAILABLE";
    }
}


// =========================================================
// DEPLOYMENT RISK CALCULATION
// Matches risk-engine/risk_engine.py
// =========================================================

function calculateRisk(
    testFailures,
    coverage,
    securityIssues,
    changedFiles,
    previousFailures
) {

    // Test failures
    const testRisk =
        Math.min(
            testFailures * 10,
            30
        );


    // Code coverage
    let coverageRisk;

    if (coverage >= 80) {

        coverageRisk = 0;

    } else if (coverage >= 60) {

        coverageRisk = 10;

    } else {

        coverageRisk = 20;
    }


    // Security issues
    const securityRisk =
        Math.min(
            securityIssues * 5,
            25
        );


    // Changed files
    const changedFilesRisk =
        Math.min(
            Math.floor(
                changedFiles / 10
            ) * 2,
            10
        );


    // Previous failures
    const previousFailureRisk =
        Math.min(
            previousFailures * 5,
            15
        );


    // Total
    const riskScore =
        testRisk +
        coverageRisk +
        securityRisk +
        changedFilesRisk +
        previousFailureRisk;


    // Decision
    let riskLevel;
    let decision;


    if (riskScore <= 30) {

        riskLevel = "SAFE";
        decision = "APPROVED";

    } else if (riskScore <= 60) {

        riskLevel = "CAUTION";
        decision = "VALIDATION_REQUIRED";

    } else {

        riskLevel = "HIGH";
        decision = "BLOCKED";
    }


    return {
        riskScore,
        riskLevel,
        decision
    };
}


// =========================================================
// ANALYZE DEPLOYMENT
// =========================================================

async function analyzeDeployment() {

    // -------------------------------------------------
    // GET FORM VALUES
    // -------------------------------------------------

    const projectName =
        document.getElementById(
            "projectName"
        ).value.trim() ||
        "Demo Project";


    const testFailures =
        Number(
            document.getElementById(
                "inputTests"
            ).value
        );


    const coverage =
        Number(
            document.getElementById(
                "inputCoverage"
            ).value
        );


    const securityIssues =
        Number(
            document.getElementById(
                "inputSecurity"
            ).value
        );


    const changedFiles =
        Number(
            document.getElementById(
                "inputChanged"
            ).value
        );


    const previousFailures =
        Number(
            document.getElementById(
                "inputPrevious"
            ).value
        );


    // -------------------------------------------------
    // VALIDATE INPUT
    // -------------------------------------------------

    if (
        testFailures < 0 ||
        coverage < 0 ||
        coverage > 100 ||
        securityIssues < 0 ||
        changedFiles < 0 ||
        previousFailures < 0
    ) {

        alert(
            "Please enter valid deployment values."
        );

        return;
    }


    // -------------------------------------------------
    // SHOW ANALYZING STATE
    // -------------------------------------------------

    const button =
        document.querySelector(
            ".deploy-btn"
        );


    button.disabled = true;

    button.textContent =
        "⏳ Analyzing Deployment...";


    // Small delay makes the demo feel like
    // a real deployment pipeline.

    await sleep(800);


    // -------------------------------------------------
    // RUN RISK ENGINE
    // -------------------------------------------------

    const result =
        calculateRisk(
            testFailures,
            coverage,
            securityIssues,
            changedFiles,
            previousFailures
        );


    // -------------------------------------------------
    // SHOW RESULT
    // -------------------------------------------------

    const resultBox =
        document.getElementById(
            "deploymentResult"
        );


    const resultBadge =
        document.getElementById(
            "resultBadge"
        );


    document.getElementById(
        "resultProject"
    ).textContent =
        projectName;


    document.getElementById(
        "resultScore"
    ).textContent =
        result.riskScore;


    document.getElementById(
        "resultLevel"
    ).textContent =
        result.riskLevel;


    document.getElementById(
        "resultDecision"
    ).textContent =
        result.decision;


    // -------------------------------------------------
    // RESULT MESSAGE
    // -------------------------------------------------

    const message =
        document.getElementById(
            "resultMessage"
        );


    if (
        result.riskLevel === "SAFE"
    ) {

        resultBadge.textContent =
            "APPROVED";


        message.textContent =
            "Deployment approved. " +
            "Risk level is within the safe threshold. " +
            "The project can proceed to deployment.";


    } else if (
        result.riskLevel === "CAUTION"
    ) {

        resultBadge.textContent =
            "VALIDATION REQUIRED";


        message.textContent =
            "Deployment requires additional validation. " +
            "The risk engine detected moderate deployment risk.";


    } else {

        resultBadge.textContent =
            "BLOCKED";


        message.textContent =
            "Deployment blocked. " +
            "The calculated risk is above the permitted threshold.";
    }


    // Make result visible
    resultBox.style.display =
        "block";


    // -------------------------------------------------
    // UPDATE RESULT STYLE
    // -------------------------------------------------

    resultBox.classList.remove(
        "safe-result",
        "caution-result",
        "high-result"
    );


    if (
        result.riskLevel === "SAFE"
    ) {

        resultBox.classList.add(
            "safe-result"
        );

    } else if (
        result.riskLevel === "CAUTION"
    ) {

        resultBox.classList.add(
            "caution-result"
        );

    } else {

        resultBox.classList.add(
            "high-result"
        );
    }


    // -------------------------------------------------
    // RESET BUTTON
    // -------------------------------------------------

    button.disabled = false;

    button.textContent =
        "🔍 Analyze & Deploy";
}


// =========================================================
// SLEEP / DEMO DELAY
// =========================================================

function sleep(milliseconds) {

    return new Promise(
        resolve =>
            setTimeout(
                resolve,
                milliseconds
            )
    );
}


// =========================================================
// HTML ESCAPING
// =========================================================

function escapeHtml(value) {

    return String(value)

        .replaceAll(
            "&",
            "&amp;"
        )

        .replaceAll(
            "<",
            "&lt;"
        )

        .replaceAll(
            ">",
            "&gt;"
        )

        .replaceAll(
            '"',
            "&quot;"
        )

        .replaceAll(
            "'",
            "&#039;"
        );
}


// =========================================================
// START DASHBOARD
// =========================================================

loadDashboard();