const BASE_URL = 'http://192.168.0.117:8000';

export async function generateCarousel({ videoUrl, slideCount }) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 300_000); // 5 min

  let response;
  try {
    response = await fetch(`${BASE_URL}/generate-carousel`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        video_url: videoUrl,
        slide_count: slideCount,
        tone: 'auto',
      }),
      signal: controller.signal,
    });
  } catch (err) {
    if (err.name === 'AbortError') {
      throw new Error('Request timed out. The pipeline is taking too long — check the backend is running.');
    }
    throw new Error(`Could not reach the server at ${BASE_URL}. Make sure the backend is running and your phone is on the same Wi-Fi.`);
  } finally {
    clearTimeout(timeout);
  }

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || 'Failed to generate carousel.');
  }

  return data;
}
