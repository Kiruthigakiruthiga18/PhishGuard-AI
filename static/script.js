
const form = document.getElementById("scanForm");
const urlInput = document.getElementById("urlInput");
const scanButton = document.getElementById("scanButton");

const result = document.getElementById("result");
const resultTitle = document.getElementById("resultTitle");
const resultMessage = document.getElementById("resultMessage");
const resultUrl = document.getElementById("resultUrl");

// Create or get the SHAP explanation section
function getExplanationBox() {
    let box = document.getElementById("shapExplanation");

    if (!box) {
        box = document.createElement("section");
        box.id = "shapExplanation";
        box.className = "shap-explanation";
        result.appendChild(box);
    }

    return box;
}

// Clear previous scan results
function clearPreviousResult() {
    resultTitle.textContent = "";
    resultMessage.textContent = "";
    resultUrl.textContent = "";

    getExplanationBox().replaceChildren();
}

// Display an error message
function showError(title, message) {
    result.classList.remove("hidden");
    clearPreviousResult();

    resultTitle.textContent = title;
    resultMessage.textContent = message;
}

// Validate URL format on the browser side
function validateUrl(input) {
    let value = input.trim();

    if (!value) {
        return {
            valid: false,
            message: "Please enter a URL."
        };
    }

    // Add a scheme when the user enters only a domain
    if (!/^[a-zA-Z][a-zA-Z\d+.-]*:\/\//.test(value)) {
        value = "https://" + value;
    }

    try {
        const parsed = new URL(value);

        // Allow only HTTP and HTTPS URLs
        if (!["http:", "https:"].includes(parsed.protocol)) {
            return {
                valid: false,
                message: "Only HTTP and HTTPS URLs are supported."
            };
        }

        const hostname = parsed.hostname;

        // Require a hostname with a plausible domain format
        if (
            !hostname ||
            hostname.includes(" ") ||
            !hostname.includes(".") ||
            hostname.startsWith(".") ||
            hostname.endsWith(".") ||
            hostname.includes("..")
        ) {
            return {
                valid: false,
                message:
                    "Enter a valid website URL, such as https://www.google.com."
            };
        }

        // Reject invalid ports
        if (parsed.port && (
            Number(parsed.port) < 1 ||
            Number(parsed.port) > 65535
        )) {
            return {
                valid: false,
                message: "Please enter a valid port number."
            };
        }

        return {
            valid: true,
            url: value
        };

    } catch {
        return {
            valid: false,
            message:
                "Enter a valid website URL, such as https://www.google.com."
        };
    }
}

form.addEventListener("submit", async function (event) {
    event.preventDefault();

    // Prevent repeated submissions while scanning
    if (scanButton.disabled) {
        return;
    }

    result.classList.remove("hidden");
    clearPreviousResult();

    const input = urlInput.value.trim();
    const validation = validateUrl(input);

    // Handle invalid input before calling Flask
    if (!validation.valid) {
        showError("Invalid URL", validation.message);
        return;
    }

    const url = input;

    resultTitle.textContent = "Scanning URL...";
    resultMessage.textContent =
        "Analysing URL with the machine learning model.";

    scanButton.disabled = true;
    scanButton.textContent = "Please wait...";

    try {
        const response = await fetch("/scan", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ url })
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.message || "URL scan failed.");
        }

        // Display prediction results
        resultTitle.textContent = data.prediction;

        resultMessage.textContent =
            `Phishing probability: ${data.phishing_probability}% | ` +
            `Legitimate probability: ${data.legitimate_probability}%. ` +
            data.message;

        resultUrl.textContent = "Scanned URL: " + data.url;

        // Display SHAP explanations
        const explanationBox = getExplanationBox();

        const heading = document.createElement("h3");
        heading.textContent =
            "Why did the model make this prediction?";
        explanationBox.appendChild(heading);

        const description = document.createElement("p");
        description.textContent =
            "Top 5 features ranked by absolute SHAP impact:";
        explanationBox.appendChild(description);

        const list = document.createElement("ul");

        if (Array.isArray(data.explanation)) {
            data.explanation.forEach((item) => {
                const listItem = document.createElement("li");

                const featureName = document.createElement("strong");
                featureName.textContent =
                    String(item.feature).replaceAll("_", " ");

                const details = document.createElement("p");
                details.textContent =
                    `Value: ${item.value} | ` +
                    `SHAP: ${item.shap_value} | ${item.effect}`;

                listItem.appendChild(featureName);
                listItem.appendChild(details);
                list.appendChild(listItem);
            });
        }

        explanationBox.appendChild(list);

    } catch (error) {
        showError(
            "Scan error",
            error.message || "Could not connect to the backend."
        );

    } finally {
        scanButton.disabled = false;
        scanButton.textContent = "Scan URL →";
    }
});
