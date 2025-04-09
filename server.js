require("dotenv").config();
const express = require("express");
const axios = require("axios");
const cors = require("cors");

const app = express();
app.use(cors());
app.use(express.json());

const PORT = process.env.PORT || 8080;

// Load API keys from environment variables
const GOOGLE_API_KEY = process.env.GOOGLE_API_KEY;
const SEARCH_ENGINE_ID = process.env.SEARCH_ENGINE_ID;
const BING_API_KEY = process.env.SERPAPI_API_KEY

// Google Search API Endpoint
app.get("/search/google", async (req, res) => {
    try {
        const query = req.query.query;
        const url = `https://www.googleapis.com/customsearch/v1?q=${query}&key=${GOOGLE_API_KEY}&cx=${SEARCH_ENGINE_ID}`;
        const response = await axios.get(url);
        res.json(response.data);
    } catch (error) {
        res.status(500).json({ error: "Error fetching Google search results" });
    }
});

// Bing Search API Endpoint
app.get("/search/bing", async (req, res) => {
    try {
        const query = req.query.query;
        const url = `https://serpapi.com/search.json?engine=bing&q=${query}&api_key=${BING_API_KEY}`;
        const response = await axios.get(url);
        res.json(response.data);
    } catch (error) {
        res.status(500).json({ error: "Error fetching Bing search results" });
    }
});

// Custom Search API Endpoint
app.get("/search/custom", async (req, res) => {
    try {
        const query = req.query.query;
        const url = ``;
        const response = await axios.get(url);
        res.json(response.data);
    } catch (error) {
        res.status(500).json({ error: "Error fetching Google search results" });
    }
});

// Start the server
app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});
