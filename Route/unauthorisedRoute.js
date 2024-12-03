const express = require('express');
const UnauthorizedEntryController = require('../controller/unauthorisedcontroller');
const router = express.Router();

// Route to handle unauthorized entry data storage
router.post('/unauthorizedentry', async (req, res) => {
    try {
        // Pass the req and res directly to the controller
        await UnauthorizedEntryController.storeUnauthorizedEntry(req, res);
    } catch (error) {
        console.error('Error storing unauthorized entry:', error);
        res.status(500).send('Error processing unauthorized entry.');
    }
});

module.exports = router;
