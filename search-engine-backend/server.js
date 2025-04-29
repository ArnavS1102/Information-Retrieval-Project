require("dotenv").config();
console.log("GOOGLE_API_KEY:", process.env.GOOGLE_API_KEY);

const express = require("express");
const axios = require("axios");
const cors = require("cors");

const app = express();
const { spawn } = require('child_process');

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


// Custom Search API Endpoint - indexed model
app.get("/search/custom/model", async (req, res) => {
    try {
        const query = req.query.query;
        const model = req.query.model;

        let response = []

        if (model == 'page_rank') {
            response = await axios.post("http://localhost:5001/search/pagerank", {
                query: query,
            });
        }
        else if (model == 'hits') {
            response = await axios.post("http://localhost:5001/search/hits", {
                query: query,
            })
        }
        else if (model == 'hybrid') {
            response = await axios.post("http://localhost:5001/search/hybrid", {
                query: query,
            })
        }
        else {
            response = await axios.post("http://localhost:5001/search/vector", {
                query: query,
            })
        }

        res.json(response.data);
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: "Error fetching custom search results" });
    }
});

// Custom Search API Endpoint - clustering
app.get("/search/custom/clustering", async (req, res) => {
    const query = req.query.query;
    const cluster = req.query.cluster

    const python = spawn("python3", ["/Users/khushiagrawal/Documents/SLIDES/SPRING'25/Information Retrieval/project/siddhi-code/main.py", query, cluster]);

    let results = "";
    python.stdout.on("data", (data) => {
        results += data.toString();
    });

    python.stderr.on("data", (data) => {
        console.error(`stderr: ${data}`);
    });

    python.on("close", (code) => {
        try {
            const parsed = JSON.parse(results);
            res.json(parsed);
        } catch (e) {
            console.error("Failed to parse Python output:", results);
            res.status(500).json({ error: "Failed to fetch custom search results" });
        }
    });
    // try {
    //     const query = req.query.query;

    //     const response = await axios.post("http://localhost:5001/search", {
    //         query: query,
    //         top_k: 5
    //     });
    //     res.json(response.data);
    // } catch (error) {
    //     console.error(error);
    //     res.status(500).json({ error: "Error fetching custom search results" });
    // }
});

// Custom Search API Endpoint - query expansion
app.get("/search/custom/expansion", async (req, res) => {

    const query = req.query.query;
    const expand_query = req.query.expand_query

    const file_path = "/Users/khushiagrawal/Documents/SLIDES/SPRING'25/Information Retrieval/project/sahiti-code/query_expansion.py"
    const combined_data = "/Users/khushiagrawal/Documents/SLIDES/SPRING'25/Information Retrieval/project/arnav-code/combined_data_new.csv"
    const rocchio_path = "/Users/khushiagrawal/Documents/SLIDES/SPRING'25/Information Retrieval/project/sahiti-code/rocchio_queries.txt"

    const python = spawn("python3", [file_path,
        "--query", query,
        "--method", expand_query,
        "--corpus_file", combined_data,
        "--queries_file", rocchio_path
    ]);

    let results = "";
    python.stdout.on("data", (data) => {
        results += data.toString();
    });

    python.stderr.on("data", (data) => {
        console.error(`stderr: ${data}`);
    });

    python.on("close", (code) => {
        try {
            const parsed = JSON.parse(results);
            res.json(parsed);
        } catch (e) {
            console.error("Failed to parse Python output:", results);
            res.status(500).json({ error: "Failed to fetch custom search results" });
        }
    });
});

// Start the server
app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});
