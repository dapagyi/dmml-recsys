import { useState, useEffect } from 'react'
import { Settings, Sun, Moon, Loader2 } from 'lucide-react';
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'

function App() {
  const [theme, setTheme] = useState('light');
  const [apiUrl, setApiUrl] = useState('https://dmml-recsys.dapagyi.dedyn.io');
  const [customApiUrl, setCustomApiUrl] = useState('');
  const [showApiInput, setShowApiInput] = useState(false);
  const [loading, setLoading] = useState(true);
  const [preprocessing, setPreprocessing] = useState(false);
  const [apiInfo, setApiInfo] = useState(null);
  const [movies, setMovies] = useState([]);
  const [selectedType, setSelectedType] = useState('item');
  const [selectedAlgorithm, setSelectedAlgorithm] = useState('');

  // Item-based inputs
  const [selectedMovie, setSelectedMovie] = useState('');
  const [topN, setTopN] = useState(10);

  // Rating-based inputs
  const [ratings, setRatings] = useState([]);
  const [ratingMovie, setRatingMovie] = useState('');
  const [ratingValue, setRatingValue] = useState(5);

  // Results
  const [recommendations, setRecommendations] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') || 'light';
    const savedApiUrl = localStorage.getItem('apiUrl');

    setTheme(savedTheme);
    document.documentElement.setAttribute('data-bs-theme', savedTheme);

    if (savedApiUrl) {
      setApiUrl(savedApiUrl);
      setCustomApiUrl(savedApiUrl);
    }

    initializeApi(savedApiUrl || apiUrl);
  }, []);

  const initializeApi = async (url) => {
    setLoading(true);
    setError(null);

    try {
      console.log('Connecting to API at:', url);

      const response = await fetch(`${url}/api/init`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });

      console.log('Response status:', response.status);

      if (!response.ok) throw new Error('Failed to connect to API');

      const data = await response.json();
      console.log('API Info:', data);
      setApiInfo(data);

      // Fetch movies data - IMPORTANT: construct full URL
      const moviesUrl = data.dataset_url.startsWith('http')
        ? data.dataset_url
        : `${url}${data.dataset_url}`;

      console.log('Fetching movies from:', moviesUrl);  // Add this debug log

      const moviesResponse = await fetch(moviesUrl, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });

      if (!moviesResponse.ok) {
        throw new Error(`Failed to fetch movies: ${moviesResponse.status}`);
      }

      const moviesData = await moviesResponse.json();
      console.log('Movies loaded:', moviesData.length);
      setMovies(moviesData);

      // Set default algorithm
      if (data.algorithms.item?.length > 0) {
        setSelectedAlgorithm(data.algorithms.item[0].id);
      }

      setLoading(false);
    } catch (err) {
      console.log('Error details:', err);
      setError(err.message);
      setLoading(false);
    }
  };

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    document.documentElement.setAttribute('data-bs-theme', newTheme);
  };

  const handleApiChange = () => {
    if (customApiUrl) {
      setApiUrl(customApiUrl);
      localStorage.setItem('apiUrl', customApiUrl);
      initializeApi(customApiUrl);
    }
    setShowApiInput(false);
  };

  const handleTypeChange = (type) => {
    setSelectedType(type);
    setRecommendations([]);
    setError(null);

    const algorithms = apiInfo.algorithms[type];
    if (algorithms?.length > 0) {
      setSelectedAlgorithm(algorithms[0].id);
    }
  };

  const addRating = () => {
    if (ratingMovie && !ratings.find(r => r.movie === ratingMovie)) {
      setRatings([...ratings, { movie: ratingMovie, rating: ratingValue }]);
      setRatingMovie('');
      setRatingValue(5);
    }
  };

  const removeRating = (movie) => {
    setRatings(ratings.filter(r => r.movie !== movie));
  };

  const getRecommendations = async () => {
    setError(null);
    setRecommendations([]);
    setPreprocessing(true);

    try {
      const algorithm = apiInfo.algorithms[selectedType].find(a => a.id === selectedAlgorithm);

      let body;
      if (selectedType === 'item') {
        body = JSON.stringify({
          item_id: selectedMovie,
          top_n: topN
        });
      } else {
        body = JSON.stringify({
          ratings: ratings.map(r => ({
            item_id: r.movie,
            rating: r.rating
          })),
          top_n: topN
        });
      }

      // Simulate preprocessing time
      await new Promise(resolve => setTimeout(resolve, 500));

      const response = await fetch(`${apiUrl}${algorithm.endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: body
      });

      if (!response.ok) throw new Error('Failed to get recommendations');

      const data = await response.json();
      setRecommendations(data.recommendations);
      setPreprocessing(false);
    } catch (err) {
      setError(err.message);
      setPreprocessing(false);
    }
  };

  const getMovieTitle = (movieId) => {
    const movie = movies.find(m => m.movieId === movieId);
    return movie ? `${movie.title} (${movie.year})` : movieId;
  };

  const isDefaultApi = apiUrl === 'https://dmml-recsys.dapagyi.dedyn.io';

  if (loading) {
    return (
      <div className="min-vh-100 d-flex align-items-center justify-content-center">
        <div className="text-center">
          <Loader2 className="spinner-border" size={48} />
          <p className="mt-3 text-muted">Connecting to API and loading data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-vh-100 py-4">
      <div className="container">
        {/* Header */}
        <div className="d-flex justify-content-between align-items-center mb-4">
          <h1 className="mb-0">Recommendation Systems Workshop</h1>
          <div className="d-flex gap-2">
            <button className="btn btn-outline-secondary" onClick={toggleTheme}>
              {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
            </button>
            <button className="btn btn-outline-secondary" onClick={() => setShowApiInput(!showApiInput)}>
              <Settings size={20} />
            </button>
          </div>
        </div>

        {/* API Settings */}
        <div className="card mb-4">
          <div className="card-body">
            <div className="d-flex align-items-center justify-content-between">
              <div>
                <small className="text-muted">Current API:</small>
                <div className="fw-semibold">
                  {isDefaultApi ? 'Default API' : apiUrl}
                </div>
              </div>
              {showApiInput && (
                <div className="d-flex gap-2 flex-grow-1 ms-3">
                  <input
                    type="text"
                    className="form-control"
                    placeholder="Enter API URL (e.g., http://localhost:8000)"
                    value={customApiUrl}
                    onChange={(e) => setCustomApiUrl(e.target.value)}
                  />
                  <button className="btn btn-primary" onClick={handleApiChange}>
                    Update
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {error && (
          <div className="alert alert-danger" role="alert">
            {error}
          </div>
        )}

        {/* Algorithm Type Selection */}
        <div className="card mb-4">
          <div className="card-body">
            <h5 className="card-title">Recommendation Mode</h5>
            <div className="btn-group w-100" role="group">
              <button
                className={`btn btn-outline-primary ${selectedType === 'item' ? 'active' : ''}`}
                onClick={() => handleTypeChange('item')}
              >
                Item-Based (Similar Items)
              </button>
              <button
                className={`btn btn-outline-primary ${selectedType === 'rating' ? 'active' : ''}`}
                onClick={() => handleTypeChange('rating')}
              >
                Rating-Based (Personalized)
              </button>
            </div>
          </div>
        </div>

        {/* Algorithm Selection */}
        <div className="card mb-4">
          <div className="card-body">
            <h5 className="card-title">Algorithm</h5>
            <select
              className="form-select"
              value={selectedAlgorithm}
              onChange={(e) => setSelectedAlgorithm(e.target.value)}
            >
              {apiInfo?.algorithms[selectedType]?.map(algo => (
                <option key={algo.id} value={algo.id}>
                  {algo.name}
                </option>
              ))}
            </select>
            {apiInfo?.algorithms[selectedType]?.find(a => a.id === selectedAlgorithm)?.description && (
              <small className="text-muted d-block mt-2">
                {apiInfo.algorithms[selectedType].find(a => a.id === selectedAlgorithm).description}
              </small>
            )}
          </div>
        </div>

        {/* Input Interface */}
        <div className="card mb-4">
          <div className="card-body">
            <h5 className="card-title">Input</h5>

            {selectedType === 'item' ? (
              <div>
                <div className="mb-3">
                  <label className="form-label">Select a movie:</label>
                  <select
                    className="form-select"
                    value={selectedMovie}
                    onChange={(e) => setSelectedMovie(e.target.value)}
                  >
                    <option value="">Choose a movie...</option>
                    {movies.map(movie => (
                      <option key={movie.movieId} value={movie.movieId}>
                        {movie.title} ({movie.year})
                      </option>
                    ))}
                  </select>
                </div>
                <div className="mb-3">
                  <label className="form-label">Number of recommendations:</label>
                  <input
                    type="number"
                    className="form-control"
                    min="1"
                    max="50"
                    value={topN}
                    onChange={(e) => setTopN(parseInt(e.target.value))}
                  />
                </div>
              </div>
            ) : (
              <div>
                <div className="mb-3">
                  <label className="form-label">Add ratings:</label>
                  <div className="d-flex gap-2 mb-2">
                    <select
                      className="form-select"
                      value={ratingMovie}
                      onChange={(e) => setRatingMovie(e.target.value)}
                    >
                      <option value="">Choose a movie...</option>
                      {movies.map(movie => (
                        <option key={movie.movieId} value={movie.movieId}>
                          {movie.title} ({movie.year})
                        </option>
                      ))}
                    </select>
                    <input
                      type="number"
                      className="form-control"
                      style={{ maxWidth: '100px' }}
                      min="1"
                      max="5"
                      step="0.5"
                      value={ratingValue}
                      onChange={(e) => setRatingValue(parseFloat(e.target.value))}
                    />
                    <button className="btn btn-primary" onClick={addRating}>
                      Add
                    </button>
                  </div>
                </div>

                {ratings.length > 0 && (
                  <div className="mb-3">
                    <label className="form-label">Your ratings:</label>
                    <div className="list-group">
                      {ratings.map(r => (
                        <div key={r.movie} className="list-group-item d-flex justify-content-between align-items-center">
                          <span>{getMovieTitle(r.movie)}</span>
                          <div className="d-flex align-items-center gap-2">
                            <span className="badge bg-primary">{r.rating} ★</span>
                            <button
                              className="btn btn-sm btn-outline-danger"
                              onClick={() => removeRating(r.movie)}
                            >
                              Remove
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="mb-3">
                  <label className="form-label">Number of recommendations:</label>
                  <input
                    type="number"
                    className="form-control"
                    min="1"
                    max="50"
                    value={topN}
                    onChange={(e) => setTopN(parseInt(e.target.value))}
                  />
                </div>
              </div>
            )}

            <button
              className="btn btn-success w-100"
              onClick={getRecommendations}
              disabled={preprocessing || (selectedType === 'item' ? !selectedMovie : ratings.length === 0)}
            >
              {preprocessing ? (
                <>
                  <Loader2 className="spinner-border spinner-border-sm me-2" />
                  Processing...
                </>
              ) : (
                'Get Recommendations'
              )}
            </button>
          </div>
        </div>

        {/* Results */}
        {recommendations.length > 0 && (
          <div className="card">
            <div className="card-body">
              <h5 className="card-title">Recommendations</h5>
              <div className="list-group">
                {recommendations.map((rec, idx) => (
                  <div key={idx} className="list-group-item d-flex justify-content-between align-items-center">
                    <div>
                      <span className="badge bg-secondary me-2">{idx + 1}</span>
                      {getMovieTitle(rec.item_id)}
                    </div>
                    <span className="badge bg-primary rounded-pill">
                      Score: {rec.score.toFixed(3)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet" />
    </div>
  );

}

export default App
