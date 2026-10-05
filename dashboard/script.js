async function loadDashboard() {
    try {
        const response = await fetch("http://localhost:5000/api/deployments");

        if (!response.ok) {
            throw new Error("Unable to load deployment data.");
        }

        const data = await response.json();

        // Update summary cards
        document.getElementById("riskScore").textContent =
            data.summary.riskScore;

        document.getElementById("riskLevel").textContent =
            data.summary.riskLevel;

        document.getElementById("decision").textContent =
            data.summary.decision;


        // Update latest deployment
        const latestTable =
            document.getElementById("latestDeploymentTable");

        latestTable.innerHTML = "";

        const latest = data.deployments[0];

        if (latest) {
            const row = document.createElement("tr");

            row.innerHTML = `
                <td>${latest.id}</td>
                <td>${latest.riskScore}</td>
                <td>${latest.riskLevel}</td>
                <td>${latest.status}</td>
            `;

            latestTable.appendChild(row);
        }


        // Update deployment history
        const table =
            document.getElementById("deploymentTable");

        table.innerHTML = "";

        data.deployments.forEach((deployment) => {

            const row = document.createElement("tr");

            row.innerHTML = `
                <td>${deployment.id}</td>
                <td>${deployment.riskScore}</td>
                <td>${deployment.decision}</td>
                <td>${deployment.status}</td>
                <td>${deployment.rollback ? "Yes" : "No"}</td>
            `;

            table.appendChild(row);
        });

    } catch (error) {

        console.error("Dashboard error:", error);

        document.getElementById("riskLevel").textContent =
            "ERROR";

        document.getElementById("decision").textContent =
            "DATA UNAVAILABLE";
    }
}


loadDashboard();