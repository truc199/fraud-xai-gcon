# Technical Specification: Advanced Fraud & xAI Pipeline Upgrades

This document synthesizes the exact mathematical formulations, algorithms, and architectures detailed in `1.md`, `2.md`, `3.md`, and `4.md` to serve as a complete implementation guide for developers and AI agents.

---

## 1. Dimensionality & Sequence Robustness (Phase 1)

### Option A: Local Hessian Spectral Dimension (LHSD) & High-Order Markov (From 1.md)
Designed to handle high-dimensional spatial spaces and short-to-medium sequence lengths.

#### Local Intrinsic Dimension (LID) via Hessian Spectral Filtering
Given a test point $x \in \mathbb{R}^D$ and local log-density function $\log p(x)$, we calculate the local Hessian matrix $H(x) = \nabla^2 \log p(x)$. We approximate the trace of the spectral filter $\Phi(H)$ using **Stochastic Lanczos Quadrature (SLQ)**:
1.  Generate $M$ random vectors $v^{(m)} \sim \mathcal{N}(0, I_D)$.
2.  For each vector, run $K$ steps of the Lanczos process on $H(x)$ to obtain a tridiagonal matrix $T_m \in \mathbb{R}^{K \times K}$ and its Ritz pairs $(\lambda_k^{(m)}, \theta_k^{(m)})$.
3.  Approximate the trace of the spectral filter:
    $$\text{Tr}(\Phi(H)) \approx \frac{1}{M} \sum_{m=1}^{M} \sum_{k=1}^{K} (\theta_{k,1}^{(m)})^2 \Phi(\lambda_k^{(m)})$$
    where $\Phi(\lambda)$ is a step function cutting off eigenvalues below a local noise threshold $\lambda_{\text{threshold}}$.

#### Second-Order Markov Transition Matrix
$$M_{(a_{t-2}, a_{t-1}), a_t} = P(a_t \mid a_{t-1}, a_{t-2})$$
$$\text{Rarity Score: } S(A) = \frac{1}{T-2} \sum_{t=3}^{T} \log M_{(a_{t-2}, a_{t-1}), a_t}$$

#### LSTM Sequence Network (For Long-Term Dependencies)
Computes hidden state $h_t$ and cell state $C_t$:
$$f_t = \sigma(W_f [h_{t-1}, x_t] + b_f)$$
$$i_t = \sigma(W_i [h_{t-1}, x_t] + b_i)$$
$$\tilde{C}_t = \tanh(W_c [h_{t-1}, x_t] + b_c)$$
$$C_t = f_t \odot C_{t-1} + i_t \odot \tilde{C}_t$$
$$o_t = \sigma(W_o [h_{t-1}, x_t] + b_o)$$
$$h_t = o_t \odot \tanh(C_t)$$

---

### Option B: Benford Significand Fraction Analysis & Switching Linear Dynamical Systems (From 2.md)
Designed for adversarial Benford evasion and non-stationary process modeling.

#### Significand Fractional Part Analysis
Rather than checking the first digit distribution $P(d)$, model the distribution of the fractional part of the significand $s$. For a transaction amount $x$, the significand base 10 is $S_{10}(x) = x \cdot 10^{-\lfloor \log_{10} x \rfloor}$.
The fractional part $f = S_{10}(x) - \lfloor S_{10}(x) \rfloor$ acts as a maximum-entropy random variable under the Benford null hypothesis:
$$f \sim \text{Uniform}(0, 1)$$
Perform a Kolmogorov-Smirnov (K-S) test of the empirical distribution of $f$ against a uniform distribution. Adversaries who match the leading digit of $x$ cannot easily preserve the uniform distribution of $f$.

#### Switching Linear Dynamical Systems (S-LDS)
Models sequences of observations $y_t$ driven by continuous states $z_t$ and discrete operational states $s_t \in \{1, \dots, K\}$:
$$z_t = A(s_t) z_{t-1} + v_t(s_t), \quad v_t(s_t) \sim \mathcal{N}(0, Q(s_t))$$
$$y_t = C(s_t) z_t + w_t(s_t), \quad w_t(s_t) \sim \mathcal{N}(0, R(s_t))$$
Transition between discrete states is modeled as a Markov chain: $P(s_t = j \mid s_{t-1} = i) = \pi_{i,j}$. Variational Bayes inference tracks continuous states $z_t$ and discrete transition states $s_t$ over time.

---

### Option C: Adversarial Sequential Detectors via Inverse Reinforcement Learning (From 4.md)
Designed to handle sequence subtrace hiding and padding.

#### Time-Varying IRL Thresholding
Formulates sequence checking as an Inverse Reinforcement Learning problem. Instead of evaluating sequence likelihood against a static transition matrix, the detector estimates a time-varying threshold $\eta_i$:
$$\eta_i \propto \mathbb{E}_{z \sim G(z)}\left[\mathcal{L}(z_{1:i} ; \theta)\right]$$
where $G(z)$ is the optimal adversarial sequence generator, and $\mathcal{L}(z_{1:i})$ is the sequence log-likelihood. 
Compute sequential distance using **Maximum Mean Discrepancy (MMD)** over a sliding window to evaluate divergence from the expected marked point process.

---

## 2. Dynamic Concept Drift & Threshold Adaptation (Phase 2)

### Option A: KELP Breathing Tree & Multivariate K-S Test (From 1.md)
Designed for online parsing of tokenized activity logs.

#### KELP Breathing Tree
*   **Entropy**: Calculate node transition entropy $H(N) = -\sum_{i} P_i \log_2 P_i$.
*   **Expansion**: If $H(N) > \tau_{\text{expand}}$, expand node: $N \to \{N_{\text{child}_1}, N_{\text{child}_2}\}$.
*   **Contraction**: If $H(N) < \tau_{\text{contract}}$, merge child nodes back into their parent.

#### Online Multivariate K-S Test
Compares current sliding window CDF $F_t(x)$ against baseline historical CDF $F_0(x)$:
$$D_{\text{KS}} = \sup_x |F_t(x) - F_0(x)|$$
Triggers threshold re-calibration if $D_{\text{KS}} > D_{\alpha}$.

---

### Option B: Dirichlet Process Gaussian Mixture Models (DPGMM) & DynAmo Trajectories (From 2.md)
Designed for non-parametric spatial cohort allocation and continuous centroid trajectory analysis.

#### Dirichlet Process Gaussian Mixture Model (DPGMM)
Rather than setting a fixed cluster size $K$, model cohorts using a Dirichlet Process prior $DP(\alpha, G_0)$. Formulated via the Chinese Restaurant Process (CRP):
$$P(\text{customer } i \text{ joins cohort } k \mid \text{existing cohorts}) = \frac{n_k}{i - 1 + \alpha}$$
$$P(\text{customer } i \text{ starts a new cohort} \mid \text{existing cohorts}) = \frac{\alpha}{i - 1 + \alpha}$$
where $n_k$ is the size of cohort $k$, and $\alpha$ is the concentration parameter. Cohorts scale automatically based on data density.

#### DynAmo Centroid Trajectory Tracker
1.  Partition time series into short sliding windows $W_1, W_2, \dots$.
2.  Extract clusters and encapsulate them using hyperbox boundaries.
3.  Calculate the trajectory of cluster centroids $C_k(t)$.
4.  Monitor the derivative of the centroid path: $\mathbf{v}_k(t) = \frac{d C_k(t)}{dt}$.
5.  If $\|\mathbf{v}_k(t)\|$ changes smoothly, update cluster centers (drift adaptation). If there is a sharp discontinuity in the trajectory derivative, trigger an alert (evasion attempt).

---

### Option C: Frobenius Norm Correlation Discrepancy - CONDOR (From 4.md)
Designed for physical/logical correlation preservation under rapid behavioral drift.

#### Frobenius Norm Discrepancy
To decouple behavioral drift from adversarial changes, compare the correlation matrices of data variables over time. Legitimate drift preserves the correlation structure (Frobenius norm remains stable), whereas adversarial manipulation shatters correlation alignments.
Calculate discrepancy between historical correlation matrix $\Sigma_0$ and current window correlation matrix $\Sigma_t$:
$$\mathcal{L}_{\text{correlation}} = \left\| \Sigma_t - \Sigma_0 \right\|_F = \sqrt{\sum_{i=1}^{D} \sum_{j=1}^{D} (\Sigma_{t, i,j} - \Sigma_{0, i,j})^2}$$
Trigger anomaly alert if $\mathcal{L}_{\text{correlation}} > \tau_{\text{correlation}}$.

---

## 3. Non-Negative PU Learning (nnPU) & Calibration (Phase 3)

### Option A: nnPU & PAYN Spy-Determited Threshold (From 1.md)
Best suited for deep-learning-based classification on positive-unlabeled datasets.

#### Non-Negative Empirical Risk Estimation (nnPU)
$$\mathcal{R}_{\text{PU}}(f) = \pi \mathcal{R}_p^+(f) + \max\left(0, \mathcal{R}_u^-(f) - \pi \mathcal{R}_p^-(f)\right)$$
This prevents empirical risk on unlabeled negatives from going negative, preventing gradient explosion.

#### PAYN (Spy-Determined Threshold) Algorithm
1.  **Inject Spies**: Select a subset $S \subset P$ where $|S| = \eta |P|$ (e.g. $\eta = 0.1$).
2.  **Noisy Mix**: Train model $f(x)$ on $P_{\text{train}} = P \setminus S$ vs $U_{\text{train}} = U \cup S$.
3.  **Find Threshold**: Evaluate predictions on $S$. Find the threshold $\tau_{\text{spy}}$ below which only $5\%$ of spies fall:
    $$\tau_{\text{spy}} = \text{Percentile}\left(\{f(s) \mid s \in S\}, 5.0\right)$$
4.  **Re-Label**: For all $u \in U$, if $f(u) < \tau_{\text{spy}}$, label $u$ as a true negative ($y = 0$).

---

### Option B: Predictive Adversarial Networks (PAN) & PU In-Context Learning (From 2.md)
Best suited for batched adversarial attacks and zero-gradient runtime adaptation.

#### Predictive Adversarial Networks (PAN)
Instead of class-conditional noise models, PAN maps mutual contamination distributions $P(X \mid Y)$:
*   **Generator ($G$)**: Selects true positive examples from the unlabeled pool $U$.
*   **Discriminator ($D$)**: Evaluates whether a sample is a labeled positive $P$ or a generator-selected positive.
*   The optimization objective minimizes the Kullback-Leibler (KL) divergence of output distributions to dynamically locate the decision boundary without prior contamination rates.

#### Positive-Unlabeled In-Context Learning (PUICL)
1.  Pre-train a Transformer model $f_\theta$ on thousands of synthetic datasets generated under various class-priors $\pi$ and causal graphs.
2.  During inference, feed the target labeled and unlabeled samples as a single input sequence $S = (x_1^L, y_1^L, \dots, x_N^U, ?)$.
3.  Execute a single forward pass through the pre-trained Transformer to output probabilities. No backpropagation occurs at test time, rendering the model immune to online gradient poisoning attacks.

---

### Option C: Rademacher Complexity Regularization (ScalePU) & Loss Optimization (From 3.md & 4.md)
Best suited for extreme label scarcity and SNAR batched contamination.

#### Rademacher Complexity Bounding (ScalePU)
Prevents model boundaries from expanding elastically around dense adversarial clusters by restricting the hypothesis space:
$$\text{Minimize} \quad \mathcal{R}_{\text{nnPU}}(f) + \lambda \cdot \hat{\mathcal{R}}_S(\mathcal{H})$$
where $\hat{\mathcal{R}}_S(\mathcal{H})$ is the empirical Rademacher complexity of the model hypothesis space $\mathcal{H}$ over dataset $S$. This restricts positive representation terms to a tight, compact uniform bound.

#### CV-based Unlabeled Optimization (CVuO)
To prevent the model from incorporating high-density adversarial anomalies during training:
1.  Split training data into $K$ cross-validation folds.
2.  During risk evaluation, sort unlabeled samples by their individual loss contribution: $\mathcal{L}_i = \ell^-(f(x_i))$.
3.  Discard the top $\gamma$ fraction of unlabeled samples with the highest losses:
    $$U_{\text{filtered}} = U \setminus \{u_i \mid \text{Loss}(u_i) > \text{Percentile}(\text{Loss}(U), 100(1-\gamma))\}$$
4.  Execute backpropagation solely on $U_{\text{filtered}}$.

---

## 4. Causal & Temporal Counterfactual Explanations (Phase 4)

### Option A: SCM Graph Enforcement & LTLp Logic Automata (From 1.md)
Focuses on structural causal dependencies and temporal process sequence rules.

#### Structural Causal Model (SCM) Backtracking
For a node $X_i$ with parent causes $\text{PA}(X_i)$ and exogenous noise $U_i$:
$$X_i = f_i(\text{PA}(X_i), U_i)$$
1.  **Abduction**: Calculate $p(U=u \mid X=x)$.
2.  **Action**: Apply Pearl's $do(T = t')$ to mutate variable $T$, enforcing $\delta_T = t' - x_T$. For immutable variables, enforce $\delta_i = 0$.
3.  **Prediction**: Update all downstream descendants $d \in \text{Descendants}(T)$ using SCM functions:
    $$x_d \leftarrow f_d(\text{PA}(X_d), U_d)$$

#### Linear Temporal Logic (LTLp) Automata
Evaluates temporal constraints (e.g. $\square(A \to \Diamond B)$) by representing them as a Buchi Automaton integrated into a genetic algorithm search:
$$\text{Fitness}(x_{\text{cf}}) = \text{Proximity}(x, x_{\text{cf}}) + P_{\text{LTL}}(x_{\text{cf}})$$
$$P_{\text{LTL}}(x_{\text{cf}}) = \begin{cases} 0 & \text{if path is accepted by the LTLp automaton} \\ \infty & \text{otherwise} \end{cases}$$

---

### Option B: Deep SCM Interventions & PINN Multi-Objective Optimization (From 2.md)
Focuses on physical dynamics constraints modeled via partial differential equations.

#### Pearl's Hierarchy Three-Step Intervention (DSCMs)
1.  **Abduction**: Infer the exogenous noise distribution $p(U \mid X)$ using bijective normalizing flows.
2.  **Action**: Substitute SCM structural equations with the counterfactual target value: $do(X_j = x_j^*)$.
3.  **Prediction**: Forward-pass the updated exogenous noise through the SCM to compute the counterfactual features.

#### Physics-Informed Neural Network (PINN) Multi-Objective Optimization
Formulates counterfactual generation as a multi-objective search solved via NSGA-II:
$$\min_{\delta} \quad \left[ \mathcal{L}_{\text{data}}(x + \delta), \mathcal{L}_{\text{physics}}(x + \delta) \right]$$
where:
*   $\mathcal{L}_{\text{data}}$: Objective to flip the classification outcome.
*   $\mathcal{L}_{\text{physics}}$: Evaluation of physical/domain constraints represented as a system of PDEs:
    $$\mathcal{L}_{\text{physics}} = \sum_c \left\| \mathcal{A}_c(x + \delta) \right\|_2^2$$
*   Weights between objectives are balanced dynamically using **Variance-Aware Relative Improvement (VARI)**.

---

### Option C: Sequential-Causal Recourse Partitioning - BRACE (From 3.md & 4.md)
Enforces Actionable Recourse by partitioning the feature space into chronological/mutable subsets.

#### Recourse Optimization on Exogenous Space
Given endogenous observed variables $X$ mapped to latent exogenous variables $U$ via structural reduced-form functions $X = F(U)$, optimize:
$$\arg \min_{x_{\text{CF}}} \quad d_U ( F^{-1}(x_{\text{CF}}), U )$$
subject to $f(x_{\text{CF}}) = y_{\text{target}}$. Distance $d_U$ is evaluated in the exogenous noise space, maintaining physical constraints.

#### Variable Partitioning
Partition the variable space $\tau = (h, s, l)$ representing history, past, and last states:
*   **Immutable Features ($I$)**: Constant values (e.g. age, account creation date). Enforce $\delta_i = 0$ by masking gradients during backpropagation:
    $$\nabla_I \mathcal{L}_{\text{search}} \leftarrow 0$$
*   **Controllable Features ($C$)**: Variables subject to bounded natural transition rates (e.g. balances, sequence position).
*   **Intervention Features ($R$)**: Directly actionable attributes modified to generate recourse paths.

---

## 5. Feedback Loop & Retraining Defenses (Phase 5)

### Option A: Non-Parametric Drift Guardians & False Negative Audits (From 1.md)
Designed for statistical anomaly loop verification.

*   **Drift Detector**: Run separate EDDM/DDM algorithms on prediction error sequences. Freeze model weights if error rates spike.
*   **Audit Sampling**: Partition the unlabeled space using K-Means and sample transactions below the threshold to perform False Negative Audits.

---

### Option B: Elastic Weight Consolidation (EWC) & Hierarchical Fallback Routing (From 2.md)
Designed for continuous learning stability and high-throughput real-time deployment.

#### Elastic Weight Consolidation (EWC)
To prevent catastrophic forgetting of historical anomaly signatures during online updates, constrain the parameter optimization path:
$$\mathcal{L}_{\text{EWC}}(\theta) = \mathcal{L}(\theta) + \sum_i \frac{\lambda}{2} F_i (\theta_i - \theta_{A,i})^2$$
where $\mathcal{L}(\theta)$ is the current loss, $F_i$ is the diagonal element of the Fisher Information Matrix calculated on historical anomaly data, and $\theta_A$ is the model parameters before retraining.

#### Hierarchical Fallback Routing Architecture
To prevent computational collapse under high-velocity telemetry (e.g. 100,000 events/sec), route transactions conditionally:

```
                  Raw Telemetry (100,000 events/sec)
                                  │
                                  ▼
┌───────────────────────────────────────────────────────────────────┐
│ Tier 1: High-Speed Vigilance (Low Latency)                        │
│ - Quantized First-Order Markov / Static Autoencoder               │
│ - Latency: < 1 microsecond                                         │
└─────────────────────────────────┬─────────────────────────────────┘
                                  │ (Filters 99% Normal Traffic)
                                  ▼
                         1% Ambiguous Events
                                  │
                                  ▼
┌───────────────────────────────────────────────────────────────────┐
│ Tier 2: Structural Awareness                                      │
│ - DynAmo Centroid Trajectories / Physics-Informed Autoencoder     │
│ - Latency: < 10 milliseconds                                      │
└─────────────────────────────────┬─────────────────────────────────┘
                                  │ (Filters Hard Anomalies)
                                  ▼
                         0.01% Complex Cases
                                  │
                                  ▼
┌───────────────────────────────────────────────────────────────────┐
│ Tier 3: Causal Intervention                                       │
│ - DSCM Causal Backtracking / PUICL / PAN Calibration               │
│ - Execution: Offline / Human Analyst Queue                        │
└───────────────────────────────────────────────────────────────────┘
```

---

### Option C: Progressive Curriculum Match, Gradient Masking, & Trajectory Auditing (From 3.md & 4.md)
Designed to protect continuous update systems against performance decay and Boiling Frog attacks.

#### Progressive Curriculum Match (FPMist)
Combats confirmation bias in self-training loops by dynamically computing class-specific acceptance thresholds using a progressive curriculum scheduler:
$$\tau_c(t) = \tau_{\text{base}, c} + (1 - \tau_{\text{base}, c}) \cdot \left(\frac{t}{T_{\text{max}}}\right)^p$$
where $t$ is the training step, $T_{\text{max}}$ is the max steps, and $p$ is a pacing parameter. Only samples whose probability exceeds $\tau_c(t)$ are incorporated into the training set.

#### Gradient Masking & Obscuration (AnomLocal)
To prevent adversaries from probing model gradients to design Boiling Frog perturbations:
*   Inject federated differential privacy noise $\sigma$ directly to computed weight gradients:
    $$\tilde{\nabla} L(\theta) = \nabla L(\theta) + \mathcal{N}(0, \sigma^2 I)$$
*   Mask low-magnitude gradients to deny attackers boundary gradient information.

#### Trajectory Auditing (ARFU-IDS)
Audits federated/continuous weight update trajectories by validating the $L_2$ norm of model weight shifts $\Delta \theta = \theta_t - \theta_{t-1}$ against a robust threshold:
$$\|\Delta \theta\|_2 \le \gamma_{\text{audit}}$$
Updates exceeding $\gamma_{\text{audit}}$ are discarded to prevent malicious step poisoning.
