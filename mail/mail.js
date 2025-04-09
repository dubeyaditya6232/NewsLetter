import nodemailer from 'nodemailer';

export const sendEmail=async(htmlContent,RECIPIENT)=> {
    
    const transporter = nodemailer.createTransport({
      service: 'gmail',
      auth: {
        user: process.env.SMTP_USER,
        pass: process.env.SMTP_PASS,
      }
    });
  
    const mailOptions = {
      from: process.env.SMTP_USER,
      to: RECIPIENT,
      subject: 'This Week in GenAI',
      html: htmlContent
    };
  
    await transporter.sendMail(mailOptions);
    console.log('Newsletter sent!');
  }