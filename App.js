import React, { useState } from 'react';

function App() {
  const [query, setQuery] = useState('');  // Store the user's query

  const [customSearchResults, setCustomSearchResults] = useState([]);
  const [googleSearchResults, setGoogleSearchResults] = useState([]);
  const [bingSearchResults, setBingSearchResults] = useState([]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [relevanceModel, setRelevanceModel] = useState('');
  const [clustering, setClustering] = useState('');
  const [queryExpand, setQueryExpand] = useState('');

  const fetchSearchResults = async (query) => {
    setLoading(true);
    setError(null);  // Reset the error state before fetching
    try {
      let customURL = '';
      let googleURL = '';
      let bingURL = '';

      setCustomSearchResults([]);
      setGoogleSearchResults([]);
      setBingSearchResults([]);

      googleURL = `http://localhost:8080/search/google?query=${query}`;
      bingURL = `http://localhost:8080/search/bing?query=${query}`;

      const googleResponse = await fetch(googleURL);
      const bingResponse = await fetch(bingURL);

      if (!googleResponse.ok) {
        throw new Error('Failed to fetch google results');
      }
      if (!bingResponse.ok) {
        throw new Error('Failed to fetch bing results');
      }

      const googleData = await googleResponse.json();
      const bingData = await bingResponse.json();

      setGoogleSearchResults(googleData.items);
      setBingSearchResults(bingData.organic_results);
    } catch (err) {
      setError(err.message);  // Handle errors
    } finally {
      setLoading(false);
    }
  };

  // Handle form submission (search)
  const handleSearch = (event) => {
    event.preventDefault();  // Prevent page reload on form submission
    if (query.trim()) {
      fetchSearchResults(query);  // Fetch search results for the entered query
    }
  };

  const customSearchEngine = (query) => {

  }

  return (
    <div class="wrapper">

      <form class="search-engine-form" onSubmit={handleSearch}>
        <div class="input-box-wrapper">
          <input
            type="text"
            class="input-box"
            value={query}
            onChange={(e) => setQuery(e.target.value)}  // Update query state
            placeholder="Enter search query..."
          />
          <button class="submit-button" type="submit" onClick={handleSearch} >Search</button>
        </div>

        <div class="radio-buttons ">
          <div class="custom-label">
            <label>
              Africa Search Engine
            </label>
            {
              <div>
                <div class="custom-radio-buttons">
                  <h4>Relevance Model Options</h4>
                  <div>
                    <label>
                      <input
                        type="radio"
                        value="page_rank"
                        checked={relevanceModel === 'page_rank'}
                        onChange={() => setRelevanceModel('page_rank')}
                      />
                      Page Rank
                    </label>
                    <label>
                      <input
                        type="radio"
                        value="hits"
                        checked={relevanceModel === 'hits'}
                        onChange={() => setRelevanceModel('hits')}
                      />
                      HITS
                    </label>
                  </div>
                </div>

                <div class="custom-radio-buttons">
                  <h4>Clustering Options</h4>
                  <div>
                    <label>
                      <input
                        type="radio"
                        value="flat"
                        checked={clustering === 'flat'}
                        onChange={() => setClustering('flat')}
                      />
                      Flat Clustering
                    </label>
                    <label>
                      <input
                        type="radio"
                        value="hierarcheal"
                        checked={clustering === 'hierarcheal'}
                        onChange={() => setClustering('hierarcheal')}
                      />
                      Hierarcheal Clustering
                    </label>
                  </div>
                </div>

                <div class="custom-radio-buttons">
                  <h4>Query Expantion Options</h4>
                  <div>
                    <label>
                      <input
                        type="radio"
                        value="association"
                        checked={queryExpand === 'association'}
                        onChange={() => setQueryExpand('association')}
                      />
                      Association
                    </label>
                    <label>
                      <input
                        type="radio"
                        value="metric"
                        checked={queryExpand === 'metric'}
                        onChange={() => setQueryExpand('metric')}
                      />
                      Metric
                    </label>
                    <label>
                      <input
                        type="radio"
                        value="scalar"
                        checked={queryExpand === 'scalar'}
                        onChange={() => setQueryExpand('scalar')}
                      />
                      Scalar
                    </label>
                  </div>
                </div>
              </div>
            }
          </div>

          <div class="custom-label">
            <label>
              Google
            </label>
            {googleSearchResults.length > 0 && (
              <div class="search-results">
                <ol>
                  {googleSearchResults.map((result, index) => (
                    <li key={index} class="each-search">
                      <h4>{result.title}</h4>
                      <a href={result.link} target="_blank" rel="noopener noreferrer">{result.link}</a>
                      <p>{result.snippet}</p>
                    </li>
                  ))}
                </ol>
              </div>
            )}

          </div>

          <div class="custom-label">
            <label>
              Bing
            </label>

            {bingSearchResults?.length > 0 && (
              <div class="search-results">
                <ol>
                  {bingSearchResults.map((result, index) => (
                    <li key={index} class="each-search">
                      <h4>{result.title}</h4>
                      <a href={result.link} target="_blank" rel="noopener noreferrer">{result.link}</a>
                      <p>{result.snippet}</p>
                    </li>
                  ))}
                </ol>
              </div>
            )}
          </div>
        </div>
      </form>

      {loading && <div class="loader-wrapper">
        <div class="loader"></div>
      </div>}

      {error && <p>Cannot load results</p>}
    </div>
  );
}

export default App;
