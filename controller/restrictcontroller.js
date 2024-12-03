const Occupancy = require('../model/restrict'); // Assuming your model file is named restrict.js

// Controller function to save occupancy data
exports.occupancyData = async (req, res) => {
    try {
        // Log the incoming request body (the occupancy data you're sending)
        console.log('Received occupancy data:', req.body);
        
        // Create a new occupancy data instance with the incoming request body
        const occupancyData = new Occupancy(req.body);

        // Save the occupancy data to the database
        await occupancyData.save();
        console.log('Data saved to database:', occupancyData);

        // Respond with the saved data and status 201
        res.status(201).json(occupancyData);
    } catch (error) {
        // Check if the error is due to validation
        if (error.name === 'ValidationError') {
            console.error('Validation Error:', error.message); // Detailed logging for validation errors
            return res.status(400).json({ error: 'Validation Error', details: error.errors });
        }

        // Log any other errors
        console.error('Error saving data:', error.message);
        res.status(500).json({ error: 'Failed to save data', message: error.message });
    }
};