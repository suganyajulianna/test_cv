// server.js
const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors'); // Ensure cors is imported
const compression = require('compression'); // Ensure compression is imported
// const server = express();

// server.use(express.json());

// Importing Routes
const restrictRoutes = require('./Route/restrictRoute');
const unauthorisedRoute = require('./Route/unauthorisedRoute');
    console.log(unauthorisedRoute)
const cameraRoute = require('./Route/Camera');
const Employee = require('./Route/Employee'); // Assuming you have Employee routes already

// Import Employee Model (Make sure you have the correct model path)
// const EmployeeModel = require('./models/Employee'); // Import your Employee model
const { log } = require('console');

// Create an instance of express
const app = express();

// Define PORT
const PORT = process.env.PORT || 3000;

// Middleware to increase the body size limit
app.use(express.json({ limit: '20mb' })); // Limit for JSON requests
app.use(express.urlencoded({ limit: '20mb', extended: true })); // Limit for URL encoded data
app.use(compression()); // Add compression middleware for response body compression
app.use(cors()); // Enable Cross-Origin Resource Sharing (CORS)

// Connect to MongoDB
mongoose.connect('mongodb+srv://srmrmpparthiban:20a8yW18xd48XYJ9@cluster0.vviu6.mongodb.net/optimus', { 
  useNewUrlParser: true, 
  useUnifiedTopology: true 
})
  .then(() => console.log('MongoDB connected'))
  .catch(err => console.error('MongoDB connection error:', err));

// Enable MongoDB Debug Mode (Optional)
mongoose.set('debug', true); // Enable MongoDB debug mode

// Routes
app.use('/api', unauthorisedRoute); // Unauthorized entry route
app.use('/api/camera', cameraRoute); // Camera routes
app.use('/api/getcamera', cameraRoute); // Get camera route (could be the same as the above)
app.use('/api/getEmployee', Employee); // Get employee details route
app.use('/api/Employee', Employee); // Employee management route
app.use('/api/restrict', restrictRoutes);



// Start the server
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
