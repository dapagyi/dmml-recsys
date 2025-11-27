import React, { useState, useEffect } from 'react';
import { Settings, Sun, Moon, Loader2 } from 'lucide-react';

const RecommendationDemo = () => {
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
    const [movieSearch, setMovieSearch] = useState('');
    const [showMovieSuggestions, setShowMovieSuggestions] = useState(false);
    const [topN, setTopN] = useState(10);

    // Rating-based inputs
    const [ratings, setRatings] = useState([]);
    const [ratingMovie, setRatingMovie] = useState('');
    const [ratingSearch, setRatingSearch] = useState('');
    const [showRatingSuggestions, setShowRatingSuggestions] = useState(false);
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

        // Close suggestions when clicking outside
        const handleClickOutside = (e) => {
            if (!e.target.closest('.movie-search')) {
                setShowMovieSuggestions(false);
                setShowRatingSuggestions(false);
            }
        };
        document.addEventListener('click', handleClickOutside);
        return () => document.removeEventListener('click', handleClickOutside);
    }, []);

    const initializeApi = async (url) => {
        setLoading(true);
        setError(null);

        try {
            const response = await fetch(`${url}/api/init`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            });

            if (!response.ok) throw new Error('Failed to connect to API');

            const data = await response.json();
            setApiInfo(data);

            const moviesUrl = data.dataset_url.startsWith('http')
                ? data.dataset_url
                : `${url}${data.dataset_url}`;

            const moviesResponse = await fetch(moviesUrl);
            const moviesData = await moviesResponse.json();
            setMovies(moviesData);

            if (data.algorithms.item?.length > 0) {
                setSelectedAlgorithm(data.algorithms.item[0].id);
            }

            setLoading(false);
        } catch (err) {
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

    const filterMovies = (search) => {
        if (!search || search.length < 2) return [];
        const searchLower = search.toLowerCase();
        return movies
            .filter(m => m.title.toLowerCase().includes(searchLower))
            .slice(0, 10);
    };

    const selectMovie = (movieId, forRating = false) => {
        if (forRating) {
            setRatingMovie(movieId);
            setRatingSearch(getMovieTitle(movieId));
            setShowRatingSuggestions(false);
        } else {
            setSelectedMovie(movieId);
            setMovieSearch(getMovieTitle(movieId));
            setShowMovieSuggestions(false);
        }
    };

    const addRating = () => {
        if (ratingMovie && !ratings.find(r => r.movie === ratingMovie)) {
            setRatings([...ratings, { movie: ratingMovie, rating: ratingValue }]);
            setRatingMovie('');
            setRatingSearch('');
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
        return movie ? `${movie.title} (${movie.year || 'N/A'})` : movieId;
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
                    <h1 className="mb-0 fs-4">Recommendation Systems Workshop</h1>
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
                                <div className="mb-3 movie-search" style={{ position: 'relative' }}>
                                    <label className="form-label">Search for a movie:</label>
                                    <input
                                        type="text"
                                        className="form-control"
                                        placeholder="Type to search movies..."
                                        value={movieSearch}
                                        onChange={(e) => {
                                            setMovieSearch(e.target.value);
                                            setShowMovieSuggestions(true);
                                        }}
                                        onFocus={() => setShowMovieSuggestions(true)}
                                    />
                                    {showMovieSuggestions && movieSearch.length >= 2 && (
                                        <div
                                            className="list-group"
                                            style={{
                                                position: 'absolute',
                                                top: '100%',
                                                left: 0,
                                                right: 0,
                                                maxHeight: '300px',
                                                overflowY: 'auto',
                                                zIndex: 1000,
                                                boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
                                            }}
                                        >
                                            {filterMovies(movieSearch).map(movie => (
                                                <button
                                                    key={movie.movieId}
                                                    type="button"
                                                    className="list-group-item list-group-item-action text-start"
                                                    onClick={() => selectMovie(movie.movieId, false)}
                                                >
                                                    {movie.title} ({movie.year || 'N/A'})
                                                </button>
                                            ))}
                                        </div>
                                    )}
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
                                    <div className="d-flex gap-2 mb-2 movie-search" style={{ position: 'relative' }}>
                                        <div style={{ flex: 1, position: 'relative' }}>
                                            <input
                                                type="text"
                                                className="form-control"
                                                placeholder="Type to search movies..."
                                                value={ratingSearch}
                                                onChange={(e) => {
                                                    setRatingSearch(e.target.value);
                                                    setShowRatingSuggestions(true);
                                                }}
                                                onFocus={() => setShowRatingSuggestions(true)}
                                            />
                                            {showRatingSuggestions && ratingSearch.length >= 2 && (
                                                <div
                                                    className="list-group"
                                                    style={{
                                                        position: 'absolute',
                                                        top: '100%',
                                                        left: 0,
                                                        right: 0,
                                                        maxHeight: '300px',
                                                        overflowY: 'auto',
                                                        zIndex: 1000,
                                                        boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
                                                    }}
                                                >
                                                    {filterMovies(ratingSearch).map(movie => (
                                                        <button
                                                            key={movie.movieId}
                                                            type="button"
                                                            className="list-group-item list-group-item-action text-start"
                                                            onClick={() => selectMovie(movie.movieId, true)}
                                                        >
                                                            {movie.title} ({movie.year || 'N/A'})
                                                        </button>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
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
};

export default RecommendationDemo;