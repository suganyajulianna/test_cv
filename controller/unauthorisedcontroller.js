const UnauthorizedEntry = require('../model/unauthorised');
const EmployeeData = require('../model/EmployeeSchema');
const CameraData = require('../model/CamereSchema');
const { sendMail } = require('../utils/mailer');
const { generateUnauthorizedEmailContent } = require('../utils/emailContentUnauthorized');




const storeUnauthorizedEntry = async (req, res) => {
    try {
        const { employee_id, Name, scenario, CameraLocationID, location_name, start_timestamp, duration, frame } = req.body;

        if (!employee_id || !CameraLocationID || !location_name || !start_timestamp || !frame) {
            return res.status(400).json({ message: "Missing required fields." });
        }

        const employee = await EmployeeData.findOne({ employee_id });
        const camera = await CameraData.findOne({ CameraLocationID });

        if (!employee && employee_id !== "Unknown") {
            return res.status(404).json({ message: "Employee not found." });
        }

        if (!camera) {
            return res.status(404).json({ message: "Camera location not found." });
        }

        const existingEntry = await UnauthorizedEntry.findOne({ EmployeeID: employee?._id || "Unknown", start_timestamp });
        if (existingEntry) {
            return res.status(409).json({ message: "Entry already exists for this timestamp." });
        }

        const newEntry = new UnauthorizedEntry({
            EmployeeID: employee?._id || "Unknown",
            Name,
            scenario,
            CameraLocationID, // Unified field
            location_name,
            start_timestamp,
            duration,
            frame,
        });

        const savedEntry = await newEntry.save();
        console.log("Saved Entry:", savedEntry);

        try {
            await handleUnauthorizedEntry(scenario, Name, CameraLocationID,start_timestamp);
        } catch (emailError) {
            console.warn("Email Notification Failed:", emailError.message);
        }

        res.status(200).json({ message: "Unauthorized entry stored successfully.", data: savedEntry });
    } catch (error) {
        console.error("Error in storeUnauthorizedEntry:", error);
        res.status(500).json({ message: "Failed to store entry.", error: error.message });
    }
};


// Helper function to handle email notification for unauthorized entry
const handleUnauthorizedEntry = async (scenario, Name, CameraLocationID, start_timestamp) => {
    try {
        console.log('Debug: generateUnauthorizedEmailContent function:', generateUnauthorizedEmailContent);
        console.log('Arguments:', { scenario, Name, CameraLocationID, start_timestamp });
        const emailContent = generateUnauthorizedEmailContent({ Name, CameraLocationID, start_timestamp });
        const subject = 'Unauthorized Entry Detected';
        const recipientEmail = 'jsuganya555@gmail.com'; // Replace with the actual recipient email
        await sendMail(recipientEmail, subject, emailContent);
    } catch (emailError) {
        console.error('Error sending email:', emailError);
        throw new Error('Error sending unauthorized entry email');
    }
};


module.exports = {
    storeUnauthorizedEntry,
};
