function generateUnauthorizedEmailContent({ Name, CameraLocationID, start_timestamp }) {
  const greeting = "Dear Team,";

  const body = `
We have detected an unauthorized entry at one of the monitored locations.

Event Details:
- Person: ${Name || "Unknown"}
- Camera Location ID: ${CameraLocationID}
- Timestamp: ${start_timestamp}

Please take immediate action to investigate and ensure the security of the area.

Best regards,
Security Monitoring System`;

  return `${greeting}\n\n${body}`;
}

module.exports = { generateUnauthorizedEmailContent };
