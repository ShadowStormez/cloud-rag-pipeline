
const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ||
  "https://cloud-rag-api.icypebble-38736748.swedencentral.azurecontainerapps.io"
).replace(/\/$/, "");

export async function askLudex(question, engine = "auto", signal) {
  const response = await fetch(`${API_BASE_URL}/ask`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      question,
      engine,
    }),
    signal,
  });

  if (!response.ok) {
    let message = `Request failed (HTTP ${response.status}).`;

    try {
      const error = await response.json();

      if (typeof error.detail === "string") {
        message = error.detail;
      }
    } catch {
      // Keep the default HTTP error message.
    }

    throw new Error(message);
  }

  const data = await response.json();

  if (typeof data.answer !== "string") {
    throw new Error("The API returned an unexpected response.");
  }

  return {
    answer: data.answer,
    sources: Array.isArray(data.sources) ? data.sources : [],
  };
}
