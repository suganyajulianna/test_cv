const nodemailer = require('nodemailer');

const transporter = nodemailer.createTransport({
    service: 'gmail', // or another email service
    auth: {
        user: 'smtp2729@gmail.com',
        pass: 'fhit ywuf vuzy tdpq',
    },
});

const sendMail = async (to, subject, content) => {
    const mailOptions = {
        from: 'smtp2729@gmail.com',
        to,
        subject,
        text: content,
    };

    await transporter.sendMail(mailOptions);
};

module.exports = { sendMail };
