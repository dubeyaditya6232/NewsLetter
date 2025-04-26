import nodemailer from 'nodemailer';

export const sendEmail = async (htmlContent, imageBuffer, RECIPIENT) => {

  const transporter = nodemailer.createTransport({
    service: 'gmail',
    auth: {
      user: process.env.SMTP_USER,
      pass: process.env.SMTP_PASS,
    }
  });

  let mailOptions;
  if (imageBuffer) {
    mailOptions = {
      from: process.env.EMAIL_USER,
      to: process.env.RECIPIENT_EMAIL,
      subject: 'This Week in GenAI',
      html: `
    <div>
      <h2>Here is your AI news update for today.</h2>
      <img src="cid:newsletterimg@cid" style="width:100%;max-width:800px;" alt="Newsletter"/>
    </div>
  `,
      attachments: [
        {
          filename: 'newsletter.jpeg',
          content: imageBuffer, 
          cid: 'newsletterimg@cid'
        }
      ]
    };
  }

  if (htmlContent) {
    mailOptions = {
      from: process.env.SMTP_USER,
      to: RECIPIENT,
      subject: 'This Week in GenAI',
      html: htmlContent
    };
  }

  await transporter.sendMail(mailOptions);
  console.log('Email sent successfully!');
}