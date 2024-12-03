const mongoose = require("mongoose");

const occupancySchema = new mongoose.Schema({
    location_id: {
        type: String,
        required: true
    },
    vacancy_status: {
        type: String,
        required: function() {
            return this.scenario === "vacancy_status"; // Only required if scenario is "vacancy_status"
        }
    },
    person_count_status: {
        type: String,
        required: function() {
            return this.scenario === "compliance_exceedance"; // Only required if scenario is "compliance_exceedance"
        }
    },
    timestamp_alert_start: {
        type: Date,
        required: true
    },
    timestamp_alert_end: {
        type: Date,
        required: true
    },
    vacant_count_duration: {
        type: Number,
        default: 0
    },
    person_count_duration: {
        type: Number,
        default: 0
    },
    vacant_frame: {
        type: String, // Store as base64 encoded string
        required: function() {
            return this.scenario === "vacancy_status"; // Only required if scenario is "vacancy_status"
        }
    },
    compliance_frame: {
        type: String, // Store as base64 encoded string
        required: function() {
            return this.scenario === "compliance_exceedance"; // Only required if scenario is "compliance_exceedance"
        }
    },
    exceeds_compliance_policy: {
        type: Boolean,
        default: false // Optional; can default to false
    },
    scenario: {
        type: String,
        enum: ["vacancy_status", "compliance_exceedance"],
        required: true // Make 'scenario' required
    }
}, { timestamps: true });

module.exports = mongoose.model("Occupancy", occupancySchema);
