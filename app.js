const API_BASE_URL = "https://1omqul7si3.execute-api.us-east-1.amazonaws.com/Stage1";
const UPLOAD_ENDPOINT = `${API_BASE_URL}/input`;
const STATUS_ENDPOINT = `${API_BASE_URL}/status`;

const fileInput = document.getElementById("fileInput");
const fileName = document.getElementById("fileName");
const statusDiv = document.getElementById("status");
const downloadDiv = document.getElementById("download");
const convertButton = document.getElementById("convertButton");
const progressBar = document.getElementById("progressBar");

fileInput.addEventListener("change", () => {
  const file = fileInput.files[0];
  fileName.textContent = file ? file.name : "Choose a document";
  clearResult();
});

async function uploadFile() {
  const file = fileInput.files[0];

  if (!file) {
    setStatus("Please select a file first.", "warning");
    return;
  }

  clearResult();
  setBusy(true);

  try {
    setProgress(18);
    setStatus("Preparing upload...");

    const uploadData = await getUploadUrl(file);
    const uploadUrl = uploadData.url || uploadData.uploadUrl || uploadData.signedUrl;

    if (!uploadUrl) {
      throw new Error("Upload URL was not returned by the API.");
    }

    setProgress(40);
    setStatus("Uploading document to S3...");
    await uploadToS3(uploadUrl, file);

    const key = uploadData.key || uploadData.fileKey || uploadData.objectKey || uploadData.Key || getKeyFromSignedUrl(uploadUrl);

    if (!key) {
      throw new Error("S3 file key was not returned by the API.");
    }

    setProgress(60);
    setStatus("Converting... (this may take up to 2 minutes)");

    const pdfUrl = await pollForPdf(key);

    setProgress(100);
    setStatus("Conversion successful!", "success");
    downloadDiv.innerHTML = `<a href="${escapeAttribute(pdfUrl)}" target="_blank" rel="noopener">Download PDF</a>`;

  } catch (error) {
    console.error(error);
    setProgress(0);
    setStatus(getErrorMessage(error), "error");
  } finally {
    setBusy(false);
  }
}

async function pollForPdf(key) {
  const baseName = key.split("/").pop().replace(/\.[^/.]+$/, ".pdf");

  const pdfUrl = `https://document-converter-bucket-v1.s3.amazonaws.com/output/${baseName}`;

  for (let i = 0; i < 24; i++) {
    await new Promise(r => setTimeout(r, 5000));

    try {
      const res = await fetch(pdfUrl, { method: "HEAD" });

      if (res.ok) {
        return pdfUrl;
      }
    } catch (e) {}
  }

  throw new Error("Conversion timed out");
}

async function getUploadUrl(file) {
  const url = new URL(UPLOAD_ENDPOINT);
  url.searchParams.set("fileName", file.name);
  url.searchParams.set("contentType", file.type || "application/octet-stream");

  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`Could not get upload URL. Status: ${response.status}`);
  }

  return response.json();
}

async function uploadToS3(uploadUrl, file) {
  const response = await fetch(uploadUrl, {
    method: "PUT",
    headers: {
      "Content-Type": file.type || "application/octet-stream"
    },
    body: file
  });

  if (!response.ok) {
    throw new Error(`S3 upload failed. Status: ${response.status}`);
  }
}

function getKeyFromSignedUrl(signedUrl) {
  try {
    const url = new URL(signedUrl);
    return decodeURIComponent(url.pathname.replace(/^\/+/, ""));
  } catch {
    return "";
  }
}

function setStatus(message, type = "") {
  statusDiv.textContent = message;
  statusDiv.className = `status ${type}`.trim();
}

function setProgress(value) {
  progressBar.style.width = `${value}%`;
}

function setBusy(isBusy) {
  convertButton.disabled = isBusy;
  convertButton.textContent = isBusy ? "Converting..." : "Convert to PDF";
}

function clearResult() {
  setStatus("");
  setProgress(0);
  downloadDiv.innerHTML = "";
}

function getErrorMessage(error) {
  if (error instanceof TypeError && error.message === "Failed to fetch") {
    return "Request blocked. Enable CORS on your API Gateway / Lambda endpoint.";
  }

  return error.message || "Error during conversion.";
}

function escapeAttribute(value) {
  return String(value).replace(/"/g, "&quot;");
}