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
  const [expandedQuery, setExpandedQuery] = useState('')

  const fetchSearchResults = async (query) => {
    setLoading(true);
    setError(null);  // Reset the error state before fetching

    try {
      let customURL = '';
      let googleURL = '';
      let bingURL = '';
      let expandeQueryURL = '';

      setCustomSearchResults([]);
      setGoogleSearchResults([]);
      setBingSearchResults([]);
      setExpandedQuery('');

      googleURL = `http://localhost:8080/search/google?query=${query}`;
      bingURL = `http://localhost:8080/search/google?query=${query}`;

      // collecting custom search engine responses
      if (clustering) {
        customURL = `http://localhost:8080/search/custom/clustering?query=${query}&cluster=${clustering}`;

        const customResponse = await fetch(customURL);
        if (!customResponse.ok) {
          throw new Error('Failed to fetch custom results');
        }

        const customData = await customResponse.json()
        setCustomSearchResults(customData);
      }
      else if (queryExpand) {
        expandeQueryURL = `http://localhost:8080/search/custom/expansion?query=${query}&expand_query=${queryExpand}`;

        const expandQueryResponse = await fetch(expandeQueryURL)
        const expandQuery = await expandQueryResponse.json()

        setExpandedQuery(expandQuery.expanded_query)

        customURL = `http://localhost:8080/search/custom/model?query=${expandQuery.expanded_query}&model=${relevanceModel}`;

        const customResponse = await fetch(customURL);
        if (!customResponse.ok) {
          throw new Error('Failed to fetch custom results');
        }

        const customData = await customResponse.json()
        setCustomSearchResults(customData.results);
      }
      else {
        customURL = `http://localhost:8080/search/custom/model?query=${query}&model=${relevanceModel}`;

        const customResponse = await fetch(customURL);
        if (!customResponse.ok) {
          throw new Error('Failed to fetch custom results');
        }

        const customData = await customResponse.json()
        setCustomSearchResults(customData.results);
      }

      // collecting google responses
      const googleResponse = await fetch(googleURL);
      if (!googleResponse.ok) {
        throw new Error('Failed to fetch google results');
      }

      const googleData = await googleResponse.json();
      setGoogleSearchResults(googleData.items);

      // collecting bing responses
      const bingResponse = await fetch(bingURL);
      if (!bingResponse.ok) {
        throw new Error('Failed to fetch bing results');
      }

      const bingData = await bingResponse.json();
      setBingSearchResults(bingData.items);

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
    else {
      setError(true)
    }
  };

  const handleResetRadioOptions = () => {
    setRelevanceModel('');
    setClustering('');
    setQueryExpand('');
    setExpandedQuery('');
    setQuery('')

    setCustomSearchResults([]);
    setGoogleSearchResults([]);
    setBingSearchResults([]);
  }

  return (
    <div className={customSearchResults.length > 0 ? "wrapper-height" : "wrapper"}>

      <form className="search-engine-form" onSubmit={handleSearch}>
        <div className="input-box-wrapper">
          <input
            type="text"
            className="input-box"
            value={query}
            onChange={(e) => setQuery(e.target.value)}  // Update query state
            placeholder="Enter search query..."
          />
          <button className="submit-button" type="submit" onClick={handleSearch} >Search</button>

          {expandedQuery &&
            <div className='expanded-query'>
              Expanded query: {expandedQuery}
            </div>}
        </div>

        <div className="radio-buttons ">
          <div className="custom-label">
            <label>
              Africa Search Engine
            </label>
            <label className='reset-label' onClick={handleResetRadioOptions} >Reset Options</label>
            {
              <div>
                <div className="custom-radio-buttons">
                  <h4>Relevance Model Options</h4>
                  <div>
                    <label>
                      <input
                        type="radio"
                        value="page_rank"
                        checked={relevanceModel === 'page_rank'}
                        onChange={() => {
                          setRelevanceModel('page_rank');
                          setClustering('');
                          setQueryExpand('');
                        }}
                      />
                      Page Rank
                    </label>
                    <label>
                      <input
                        type="radio"
                        value="hits"
                        checked={relevanceModel === 'hits'}
                        onChange={() => {
                          setRelevanceModel('hits');
                          setClustering('');
                          setQueryExpand('');
                        }}
                      />
                      HITS
                    </label>
                    <label>
                      <input
                        type="radio"
                        value="hybrid"
                        checked={relevanceModel === 'hybrid'}
                        onChange={() => {
                          setRelevanceModel('hybrid');
                          setClustering('');
                          setQueryExpand('');
                        }}
                      />
                      Hybrid
                    </label>
                  </div>
                </div>

                <div className="custom-radio-buttons">
                  <h4>Clustering Options</h4>
                  <div>
                    <label>
                      <input
                        type="radio"
                        value="kmeans"
                        checked={clustering === 'kmeans'}
                        onChange={() => {
                          setClustering('kmeans');
                          setRelevanceModel('');
                          setQueryExpand('');
                        }}
                      />
                      Flat Clustering
                    </label>
                    <label>
                      <input
                        type="radio"
                        value="agglo"
                        checked={clustering === 'agglo'}
                        onChange={() => {
                          setClustering('agglo');
                          setRelevanceModel('');
                          setQueryExpand('');
                        }}
                      />
                      Hierarchical Clustering
                    </label>
                  </div>
                </div>

                <div className="custom-radio-buttons">
                  <h4>Query Expantion Options</h4>
                  <div>
                    <label>
                      <input
                        type="radio"
                        value="association"
                        checked={queryExpand === 'association'}
                        onChange={() => {
                          setQueryExpand('association');
                          setRelevanceModel('');
                          setClustering('');
                        }}
                      />
                      Association
                    </label>
                    <label>
                      <input
                        type="radio"
                        value="metric"
                        checked={queryExpand === 'metric'}
                        onChange={() => {
                          setQueryExpand('metric');
                          setRelevanceModel('');
                          setClustering('');
                        }}
                      />
                      Metric
                    </label>
                    <label>
                      <input
                        type="radio"
                        value="scalar"
                        checked={queryExpand === 'scalar'}
                        onChange={() => {
                          setQueryExpand('scalar');
                          setRelevanceModel('');
                          setClustering('');
                        }}
                      />
                      Scalar
                    </label>
                  </div>
                </div>
              </div>
            }

            {customSearchResults?.length > 0 && (
              <div className="search-results">
                <ol>
                  {customSearchResults.map((result, index) => (
                    <li key={index} className="each-search">
                      <h4>{result.title}</h4>
                      <a href={result.url} target="_blank" rel="noopener noreferrer">{result.url}</a>
                      <p>{result.meta_description}</p>
                    </li>
                  ))}
                </ol>
              </div>
            )}
          </div>

          <div className="custom-label">
            <label>
              Google
            </label>
            {googleSearchResults.length > 0 && (
              <div className="search-results">
                <ol>
                  {googleSearchResults.map((result, index) => (
                    <li key={index} className="each-search">
                      <h4>{result.title}</h4>
                      <a href={result.link} target="_blank" rel="noopener noreferrer">{result.link}</a>
                      <p>{result.snippet}</p>
                    </li>
                  ))}
                </ol>
              </div>
            )}

          </div>
          <div className="custom-label">
            <label>
              Bing
            </label>

            {bingSearchResults?.length > 0 && (
              <div className="search-results">
                <ol>
                  {bingSearchResults.map((result, index) => (
                    <li key={index} className="each-search">
                      <h4>{result.title}</h4>
                      <div>
                        <a href={result.link} target="_blank" rel="noopener noreferrer">{result.link}</a>
                      </div>
                      <p>{result.snippet}</p>
                    </li>
                  ))}
                </ol>
              </div>
            )}
          </div>
        </div>

      </form>

      {loading && <div className="loader-wrapper">
        <div className="loader"></div>
      </div>}

      {error && <p>Cannot load results</p>}
    </div>
  );
}

export default App;
