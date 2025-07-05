## Short Description

This is the code used in my paper exploring the Vickrey-Clarke-Groves (VCG) mechanism applied to dynamic (i.e. time-varying constraints and real-time human decision-making) resource allocation in large operations. The original paper focuses on amusement parks, nevertheless the core principles are broadly generalizable; as far as I know, this is the first paper of its kind in the Market Design literature.

The repository implements an extensive multi-agent simulation with stochastic visitor dynamics and leverages combinatorial auction theory to achieve Pareto-efficient outcomes. Hence, it provides a computationally tractable solution to a multi-dimensional resource allocation problem.

## Core Components

### 1. Agent Valuation Functions
```
V(a,r,t) = α × Pᵣ + β × (Rₐ + Wₐ) - γ × Bᵢ + δ
```

Where:
- **V(a,r,t)**: Agent a's valuation for expedited pass on ride r at time t
- **Pᵣ**: Ride popularity index (derived from empirical park data)
- **Rₐ**: Agent's individual ride preference coefficient
- **Wₐ**: Agent's wait time sensitivity threshold
- **Bᵢ**: Time-dependent bundle penalty factor
- **δ**: Stochastic noise term (prevents identical valuations)

### 2. Queue Dynamics
```
Qₜ₊₁(r) = max(Qₜ(r) + Aₜ - C, 0)
Eₜ₊₁(r) = max(Eₜ(r) + Aₜᵉ - Cᵉ, 0)
```

**Standard and Expedited Queue Evolution:**
- **Qₜ(r)**: Standard queue length for ride r at time t
- **Eₜ(r)**: Expedited queue length for ride r at time t
- **Aₜ, Aₜᵉ**: Arrival rates (Poisson distributed)
- **C, Cᵉ**: Service capacities (deterministic)

### 3. Stochastic Arrival Process
```
Aₜ = Poisson(λₜ), λₜ = (N × pₕ)/60
```

**Temporal Arrival Distribution:**
- **λₜ**: Time-dependent arrival rate
- **N**: Total daily visitor population
- **pₕ**: Hourly arrival percentage (non-uniform distribution)

### 4. VCG Implementation

**Social Welfare Maximization:**
```
max Σᵢ Σⱼ vᵢⱼ × xᵢⱼ
```

**Subject to capacity constraints:**
```
Σᵢ xᵢⱼ ≤ kⱼ ∀j
```

**Pricing Rule:**
```
pᵢ = Σⱼ≠ᵢ vⱼ(S₋ᵢ) - Σⱼ≠ᵢ vⱼ(S)
```

Where S is the optimal allocation and S₋ᵢ is optimal allocation without agent i.

### 5. Agent Behavioral Dynamics
```
Agent_Behaviour(i) = {
    stay_time_preference: Normal(μ, σ),
    allow_repeats: Binary,
    ride_preference: p,
    wait_threshold: θ
}
```

**Choice Function:**
```
Choose(i) = {
    Ride if u < pᵣᵢdₑ,
    Activity otherwise
}
```

### 6. Load Distribution Algorithm
```
LoadGuests(r) = min(capacity, |Qₜ(r)|)
ExpLoadGuests(r) = min(capacity × expedited_ratio, |Eₜ(r)|)
```

**Capacity Allocation:**
```
Load(r) = {
    Standard: min(capacity - expedited_seats, |Qₜ(r)|),
    Expedited: min(expedited_seats, |Eₜ(r)|)
}
```

## Relevant Features

### Behavioral Modeling
- **Heterogeneous Agents**: Distinct preference distributions
- **Bounded Rationality**: Approximates actual decision-making closely through stochastic noise
- **Preference Evolution**: Time-dependent valuation adjustments

### Combinatorial Optimization
- **Bundle Preferences**: Agents bid on attraction packages with temporal constraints
- **Weak Preference Ordering**: B(a,i) ≥ B(a,i') for all agents a and bundles i ≠ i'
- **Multi-dimensional Resource Constraints**: Time-slot and capacity limitations

## Foundations in the literature
- **Strategy-Proofness**: VCG mechanism ensures truthful bidding equilibrium
- **Individual Rationality**: Agents never pay above their true valuations
- **Pareto Efficiency**: No reallocation improves welfare without harm
- **Monotonicity**: Higher valuations yield weakly better allocations
- **Revenue Properties**: Second-price auction characteristics are preserved
- **Tractability**: Polynomial-time approximation available
- **Convergence**: Monte Carlo reliability bounds
- **Sensitivity**: Robustness is validated across parameter variations

### Relevance and Potential Applications (beyond my paper)
- **Mechanism Design/Operations Research**: Provides an open-source preliminary testing framework for validation and testing of Auction Theory hypotheses, adaptable to multiple problems in and outside the Market Design literature.
- **Industry**: Dynamic pricing with capacity constraints (revenue management), queue and customer experience optimization (service ops), and optimal allocations under time-evolving, non-deterministic preferences or uncertainty (resource allocation)


## Citation

```bibtex
@article{ramirez2024dynamic,
  title={Dynamic Resource Allocation Systems in Large Operations: Fixing the Genie},
  author={Ramirez, Estefano},
  institution={University of Chicago},
  year={2024}
}
```

Please refer to OPR:Market Design Finalized.pdf for the full paper.

MIT License | **Author**: Estefano Ramirez | **Email**: eramirezd@uchicago.edu
