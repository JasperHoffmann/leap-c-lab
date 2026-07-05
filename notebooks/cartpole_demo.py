"""leap-c-lab — CartPole Demo

This notebook demonstrates a closed-loop MPC rollout using leap-c-lab's
cartpole planner and environment.
"""

import marimo

__generated_with = "0.13.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        # CartPole MPC Demo

        This notebook runs a closed-loop rollout of a CartPole MPC problem
        using `leap-c-lab`'s pre-built controller and environment.

        The CartPole is a classic control problem: balance a pole on a
        moving cart by applying horizontal forces.
        """
    )
    return


@app.cell
def _():
    import numpy as np
    import torch

    from leapc_lab import create_controller, create_env
    return create_controller, create_env, np, torch


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## Create controller and environment

        We use the default cartpole controller and environment from `leap-c-lab`.
        The underlying planner generates C code via acados for fast MPC solves.
        """
    )
    return


@app.cell
def _(create_controller, create_env):
    controller = create_controller("cartpole")
    env = create_env("cartpole")
    return controller, env


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## Closed-loop rollout

        Run the MPC controller in a closed loop with the environment for
        a fixed number of steps.
        """
    )
    return


@app.cell
def _(controller, env, np, torch):
    N_STEPS = 100
    obs, _ = env.reset(seed=42)
    trajectory = [obs]
    ctx = None

    for step in range(N_STEPS):
        obs_tensor = torch.as_tensor(obs, dtype=torch.float32).unsqueeze(0)
        ctx, action = controller(obs_tensor, ctx=ctx)
        action = action.squeeze(0).detach().numpy()
        obs, reward, terminated, truncated, _ = env.step(action)
        trajectory.append(obs)
        if terminated or truncated:
            break

    trajectory = np.array(trajectory)
    f"Rolled out {len(trajectory)} steps"
    return N_STEPS, trajectory


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## Visualize the trajectory

        Plot the cart position and pole angle over the rollout.
        """
    )
    return


@app.cell
def _(trajectory):
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    axes[0].plot(trajectory[:, 0], label="cart position")
    axes[0].set_ylabel("x")
    axes[0].legend()

    axes[1].plot(trajectory[:, 2], label="pole angle")
    axes[1].set_ylabel("theta")
    axes[1].legend()

    fig.suptitle("CartPole MPC Trajectory")
    fig.tight_layout()
    fig
    return fig, plt


if __name__ == "__main__":
    app.run()
