const express = require("express");
const cors = require('cors');
const bodyParser = require("body-parser");
const urlencodedParser = bodyParser.urlencoded({ extended: false });


const app = express();
const router = express.Router();

const corsOptions = {
    origin: [process.env.FRONTEND_URL],
    credentials: true,
    // methods: allowedMethods.join(',')
}

// app.use(cors(corsOptions));
app.use(cors());
app.use(urlencodedParser);
app.use(bodyParser.json());

// app.options('*', cors(corsOptions));
// app.options('*', cors());

//Index Page (Home public page)
app.get('/', function (req, res) {
    res.send('<html><title>Backend API</title><body>This project provides only backend API support</body></html>');
    res.end();
});

app.get('/chat', function (req, res) {
    res.send({message:'blah'});
    res.end();
});

module.exports = app;