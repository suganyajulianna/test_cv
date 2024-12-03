const express = require('express');
const restrictController = require('../controller/restrictcontroller'); // Adjust the path as necessary

const router = express.Router();

// POST route to add detection data
router.post('/', restrictController.occupancyData);



module.exports = router;