const multer = require('multer');

// Multer setup for memory storage (store the file in memory as a buffer)
const storage = multer.memoryStorage();

const upload = multer({ storage: storage });

module.exports = { upload };

