function generateEmailContent({ Name, employee_id, isUnknown, CameraLocationID, unauthorizedEntry, missingItems = [] }) {
    const greeting = unauthorizedEntry
        ? "Warning,"
        : isUnknown
        ? "Hello,"
        : `Hello, ${Name},`;

    const body = unauthorizedEntry
        ? `An unauthorized entry has been detected.`
        : isUnknown
        ? `An unknown person has entered the premises.`
        : `Here's the current status of items:`; // Fallback if no entry flags are triggered

    const unauthorizedInfo = unauthorizedEntry
        ? `Unauthorized access detected at Camera Location: ${CameraLocationID}.`
        : '';

    const unknownPersonInfo = isUnknown
        ? `An unknown person was detected at Camera Location: ${CameraLocationID}.`
        : '';

    const itemStatus = missingItems.length > 0
        ? missingItems
              .map(item => `- ${item.name}: ${item.isPresent ? 'Present' : 'Missing'}`)
              .join('\n')
        : '';

    const footer = `
Please take appropriate action.

Regards,
Security & Safety Management System`;

    return `${greeting}\n\n${body}\n\n${unauthorizedInfo}\n\n${unknownPersonInfo}\n\n${itemStatus}\n\n${footer}`;
}

module.exports = generateEmailContent;
