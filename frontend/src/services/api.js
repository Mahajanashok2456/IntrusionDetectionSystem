const API_BASE_URL = "http://127.0.0.1:8000";

export const generateCSV = async (numSamples, batchSize = 32) => {
  const response = await fetch(`${API_BASE_URL}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ num_samples: numSamples, batch_size: batchSize }),
  });

  if (!response.ok) throw new Error("Failed to generate CSV");

  return response.blob();
};

export const predictCSV = async (file) => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/predict`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) throw new Error("Failed to process prediction");

  return response.blob();
};
