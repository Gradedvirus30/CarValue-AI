import { useEffect, useState } from "react";
import "./App.css";

function App() {
  const [formData, setFormData] = useState({
    brand: "",
    model: "",
    vehicle_age: "",
    km_driven: "",
    seller_type: "",
    fuel_type: "",
    transmission_type: "",
    mileage: "",
    engine: "",
    max_power: "",
    seats: "",
  });

  const [options, setOptions] = useState(null);
  const [predictedPrice, setPredictedPrice] = useState(null);
  const [marketRange, setMarketRange] = useState(null);
  const [loadingOptions, setLoadingOptions] = useState(true);
  const [predicting, setPredicting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadOptions = async () => {
      try {
        const response = await fetch(
          const API_URL = import.meta.env.VITE_API_URL;
        );

        if (!response.ok) {
          throw new Error("Failed to load car options");
        }

        const data = await response.json();
        setOptions(data);
      } catch (error) {
        console.error(error);
        setError(
          "Could not connect to the prediction server."
        );
      } finally {
        setLoadingOptions(false);
      }
    };

    loadOptions();
  }, []);

  const handleChange = (event) => {
    const { name, value } = event.target;

    setFormData({
      ...formData,
      [name]: value,
      ...(name === "brand" && { model: "" }),
    });

    setPredictedPrice(null);
    setError("");
  };

  const formatINR = (value) =>
  new Intl.NumberFormat("en-IN", {
    maximumFractionDigits: 0,
  }).format(value);

  const handleSubmit = async (event) => {
    event.preventDefault();

    setPredicting(true);
    setPredictedPrice(null);
    setMarketRange(null);
    setError("");

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/predict",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            ...formData,
            vehicle_age: Number(formData.vehicle_age),
            km_driven: Number(formData.km_driven),
            mileage: Number(formData.mileage),
            engine: Number(formData.engine),
            max_power: Number(formData.max_power),
            seats: Number(formData.seats),
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Prediction request failed");
      }

      const data = await response.json();
      setPredictedPrice(data.predicted_price);
      setMarketRange(data.market_range);

    } catch (error) {
      console.error(error);
      setError(
        "Unable to generate an estimate. Please try again."
      );
    } finally {
      setPredicting(false);
    }
  };

  if (loadingOptions) {
    return (
      <div className="loading-screen">
        <div className="loading-mark">CV</div>
        <p>Preparing your estimator...</p>
      </div>
    );
  }

  return (
    <main className="app-shell">
      <nav className="navbar">
        <div className="brand-mark">
          <span className="brand-icon">CV</span>

          <div>
            <span className="brand-name">CARVALUE</span>
            <span className="brand-subtitle">
              INTELLIGENT VALUATION
            </span>
          </div>
        </div>

        <div className="nav-status">
          <span className="status-dot"></span>
          MODEL ONLINE
        </div>
      </nav>

      <section className="hero-layout">
        <div className="hero-content">
          <p className="eyebrow">ML-POWERED VALUATION</p>

          <h1>
            Know what your
            <span> car is worth.</span>
          </h1>

          <p className="hero-description">
            Get an instant market value estimate based on your
            vehicle's specifications and patterns learned from
            more than 15,000 used-car listings.
          </p>

          <div className="stats-row">
            <div className="stat">
              <span className="stat-value">0.9388</span>
              <span className="stat-label">MODEL R² SCORE</span>
            </div>

            <div className="stat-divider"></div>

            <div className="stat">
              <span className="stat-value">15K+</span>
              <span className="stat-label">VEHICLES ANALYSED</span>
            </div>

            <div className="stat-divider"></div>

            <div className="stat">
              <span className="stat-value">11</span>
              <span className="stat-label">VALUATION FACTORS</span>
            </div>
          </div>

          <div className="model-note">
            <span className="note-line"></span>

            <p>
              Powered by a Random Forest model trained on 15,000+ real used-car listings.
            </p>
          </div>
        </div>

        <div className="estimator-card">
          <div className="card-header">
            <div>
              <p className="card-kicker">VEHICLE DETAILS</p>
              <h2>Estimate your car</h2>
            </div>

            <span className="step-badge">01</span>
          </div>

          {error && <div className="error-message">{error}</div>}

          <form onSubmit={handleSubmit}>
            <div className="form-grid">
              <Field label="Brand">
                <select
                  name="brand"
                  value={formData.brand}
                  onChange={handleChange}
                  required
                >
                  <option value="">Select brand</option>

                  {options?.brands.map((brand) => (
                    <option key={brand} value={brand}>
                      {brand}
                    </option>
                  ))}
                </select>
              </Field>

              <Field label="Model">
                <select
                  name="model"
                  value={formData.model}
                  onChange={handleChange}
                  disabled={!formData.brand}
                  required
                >
                  <option value="">Select model</option>

                  {formData.brand &&
                    options?.models_by_brand[
                      formData.brand
                    ]?.map((model) => (
                      <option key={model} value={model}>
                        {model}
                      </option>
                    ))}
                </select>
              </Field>

              <Field label="Vehicle Age" suffix="years">
                <input
                  type="number"
                  name="vehicle_age"
                  min="0"
                  value={formData.vehicle_age}
                  onChange={handleChange}
                  placeholder="e.g. 5"
                  required
                />
              </Field>

              <Field label="Distance Driven" suffix="km">
                <input
                  type="number"
                  name="km_driven"
                  min="0"
                  value={formData.km_driven}
                  onChange={handleChange}
                  placeholder="e.g. 50000"
                  required
                />
              </Field>

              <Field label="Seller Type">
                <select
                  name="seller_type"
                  value={formData.seller_type}
                  onChange={handleChange}
                  required
                >
                  <option value="">Select type</option>

                  {options?.seller_types.map((type) => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                </select>
              </Field>

              <Field label="Fuel Type">
                <select
                  name="fuel_type"
                  value={formData.fuel_type}
                  onChange={handleChange}
                  required
                >
                  <option value="">Select fuel</option>

                  {options?.fuel_types.map((type) => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                </select>
              </Field>

              <Field label="Transmission">
                <select
                  name="transmission_type"
                  value={formData.transmission_type}
                  onChange={handleChange}
                  required
                >
                  <option value="">Select transmission</option>

                  {options?.transmission_types.map((type) => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                </select>
              </Field>

              <Field label="Mileage" suffix="km/l">
                <input
                  type="number"
                  step="any"
                  min="0"
                  name="mileage"
                  value={formData.mileage}
                  onChange={handleChange}
                  placeholder="e.g. 20"
                  required
                />
              </Field>

              <Field label="Engine" suffix="cc">
                <input
                  type="number"
                  min="0"
                  name="engine"
                  value={formData.engine}
                  onChange={handleChange}
                  placeholder="e.g. 1197"
                  required
                />
              </Field>

              <Field label="Max Power" suffix="bhp">
                <input
                  type="number"
                  step="any"
                  min="0"
                  name="max_power"
                  value={formData.max_power}
                  onChange={handleChange}
                  placeholder="e.g. 82"
                  required
                />
              </Field>

              <Field label="Seats">
                <input
                  type="number"
                  min="1"
                  name="seats"
                  value={formData.seats}
                  onChange={handleChange}
                  placeholder="e.g. 5"
                  required
                />
              </Field>
            </div>

            <button
              className="predict-button"
              type="submit"
              disabled={predicting}
            >
              <span>
                {predicting
                  ? "CALCULATING VALUE..."
                  : "ESTIMATE MARKET VALUE"}
              </span>

              {!predicting && <span className="button-arrow">→</span>}
            </button>
          </form>

          {predictedPrice !== null && (
            <div className="result-card">
              <div>
                <p className="result-label">
                  ESTIMATED MARKET VALUE
                </p>

                <p className="result-price">
                  ₹{formatINR(predictedPrice)}
                </p>

                {marketRange && (
                  <div className="market-range">
                    <p className="range-title">
                      ESTIMATED MARKET RANGE
                    </p>

                    <p className="range-value">
                      ₹{formatINR(marketRange.lower)} – ₹{formatINR(marketRange.upper)}
                    </p>
                  </div>
                )}
              </div>

              <div className="result-badge">ESTIMATE</div>
            </div>
          )}
        </div>
      </section>

      <footer>
        <span>CARVALUE © 2026</span>
        <span>ML-BASED ESTIMATE · NOT A FORMAL APPRAISAL</span>
      </footer>
    </main>
  );
}

function Field({ label, suffix, children }) {
  return (
    <label className="field">
      <span className="field-label">{label}</span>

      <div className="input-wrapper">
        {children}
        {suffix && <span className="input-suffix">{suffix}</span>}
      </div>
    </label>
  );
}

export default App;