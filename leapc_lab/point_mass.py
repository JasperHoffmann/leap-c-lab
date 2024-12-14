"""
linear system
"""

from typing import Any

import casadi as cs
import numpy as np
import pygame
from acados_template import AcadosModel, AcadosOcp
from casadi.tools import struct_symSX
from pygame import draw, gfxdraw

from leap_c.examples.render_utils import draw_arrow, draw_ellipse_from_eigen
from leap_c.mpc import MPC
from leap_c.ocp_env import OCPEnv


from leap_c.examples.util import (
    find_param_in_p_or_p_global,
    translate_learnable_param_to_p_global,
)


class PointMassMPC(MPC):
    """MPC for a two-dimensional point mass with a linear dynamics model."""

    def __init__(
        self,
        params: dict[str, np.ndarray] | None = None,
        learnable_params: list[str] | None = None,
        N_horizon: int = 20,
        discount_factor: float = 0.99,
        n_batch: int = 1,
    ):
        if params is None:
            params = {
                "m": np.array([1.0]),  # mass [kg]
                "c": np.array([0.1]),  # drag coefficient [N⋅s/m]
                "Q": np.diag([1.0, 1.0, 0.1, 0.1]),  # state cost
                "R": np.diag([1.0, 1.0]),  # control cost
            }

        learnable_params = learnable_params if learnable_params is not None else []

        ocp = export_parametric_ocp(
            param=params, learnable_params=learnable_params, N_horizon=N_horizon
        )

        configure_ocp_solver(ocp)

        self.given_default_param_dict = params

        super().__init__(ocp=ocp, discount_factor=discount_factor, n_batch=n_batch)


class PointMassOcpEnv(OCPEnv):
    """The idea is that the linear system describes a point mass that is pushed by a hidden force (noise)
    and the agent is required to learn to control the point mass in such a way that this force does not push
    the point mass over its boundaries (the constraints) while still minimizing the distance to the origin and
    minimizing control effort.
    """

    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 30}

    mpc: PointMassMPC

    def __init__(
        self,
        mpc: PointMassMPC,
        dt: float = 0.01,
        max_time: float = 10.0,
        render_mode: str | None = None,
    ):
        super().__init__(
            mpc,
            dt=dt,
            max_time=max_time,
        )

        # Will be added after doing a step.
        self.current_noise = None

        # For rendering
        # self.window_size = 512  # The size of the PyGame window
        if render_mode is not None:
            raise NotImplementedError("Rendering is not implemented yet.")
        # if not (render_mode is None or render_mode in self.metadata["render_modes"]):
        #     raise ValueError(
        #         f"render_mode must be one of {self.metadata['render_modes']}"
        #     )
        # self.render_mode = render_mode
        # self.window = None
        # self.clock = None
        # self.state_trajectory = None
        # self.action_to_take = None

    def step(self, action: np.ndarray) -> tuple[Any, float, bool, bool, dict]:
        """Execute the dynamics of the linear system and push the resulting state with a random noise.
        If rendering is turned on, it will render the state BEFORE taking the step."""
        self.action_to_take = action
        frame = None
        # if self.render_mode == "human" or self.render_mode == "rgb_array":
        #     frame = self.render()
        o, r, term, trunc, info = super().step(
            action
        )  # o is the next state as np.ndarray, next parameters as MPCParameter
        info["frame"] = frame

        state = o[0].copy()
        state[-2:] += self.current_noise
        self.x = state
        self.current_noise = self.next_noise()
        o = (state, o[1])

        if state not in self.state_space:
            r -= 1e2
            term = True

        return o, r, term, trunc, info

    def reset(
        self, *, seed: int | None = None, options: dict | None = None
    ) -> tuple[Any, dict]:  # type: ignore
        res = super().reset(seed=seed, options=options)
        self.state_trajectory = None
        self.action_to_take = None
        self.current_noise = self.next_noise()
        return res

    def next_noise(self) -> float:
        """Return the next noise to be added to the state."""
        if self._np_random is None:
            raise ValueError("First, reset needs to be called with a seed.")
        return self._np_random.uniform(-0.1, 0, size=2)

    def init_state(self):
        return self.mpc.ocp.constraints.x0.astype(dtype=np.float32)


def _create_cont_A_matrix(m: float | cs.SX, c: float | cs.SX):
    """Create discrete-time state transition matrix."""

    if isinstance(m, float):
        return np.array(
            [
                [0, 0, 1.0, 0],
                [0, 0, 0, 1.0],
                [0, 0, -(c / m), 0],
                [0, 0, 0, -(c / m)],
            ]
        )
    else:
        return cs.vertcat(
            cs.horzcat(0, 0, 1.0, 0),
            cs.horzcat(0, 0, 0, 1.0),
            cs.horzcat(0, 0, -(c / m), 0),
            cs.horzcat(0, 0, 0, -(c / m)),
        )


def _create_cont_B_matrix(m: float | cs.SX):
    """Create discrete-time input matrix."""
    if isinstance(m, float):
        return np.array([[0, 0], [0, 0], [1.0 / m, 0], [0, 1.0 / m]])
    else:
        return cs.vertcat(
            cs.horzcat(0, 0),
            cs.horzcat(0, 0),
            cs.horzcat(1.0 / m, 0),
            cs.horzcat(0, 1.0 / m),
        )


def _create_cont_b_matrix(m: float | cs.SX, c: float | cs.SX):
    """Create discrete-time input matrix."""
    if isinstance(m, float):
        return np.array([0, 0, 0, 0])
    else:
        return cs.vertcat(0, 0, 0, 0)


def _disc_dyn_expr(model: AcadosModel, dt: float):
    """
    Define the discrete dynamics function expression.
    """
    x = model.x
    u = model.u

    param = find_param_in_p_or_p_global(["m", "c"], model)

    A = _create_cont_A_matrix(param["m"], param["c"])
    B = _create_cont_B_matrix(param["m"])
    b = _create_cont_b_matrix(param["m"], param["c"])

    return x + dt * (A @ x + B @ u + b)


def cost_expr_ext_cost(model: AcadosModel):
    """
    Define the external cost function expression.
    """
    x = model.x
    u = model.u
    param = find_param_in_p_or_p_global(["Q", "R"], model)

    return 0.5 * (cs.transpose(x) @ param["Q"] @ x + cs.transpose(u) @ param["R"] @ u)


def cost_expr_ext_cost_0(model: AcadosModel):
    """
    Define the external cost function expression at stage 0.
    """

    return cost_expr_ext_cost(model)


def cost_expr_ext_cost_e(model: AcadosModel, param: dict[str, np.ndarray]):
    """
    Define the external cost function expression at the terminal stage as the solution of the discrete-time algebraic Riccati
    equation.
    """

    x = model.x
    param = find_param_in_p_or_p_global(["Q", "R"], model)

    return 0.5 * (cs.transpose(x) @ param["Q"] @ x)


def configure_ocp_solver(
    ocp: AcadosOcp,
):
    ocp.solver_options.tf = ocp.solver_options.N_horizon
    ocp.solver_options.integrator_type = "DISCRETE"
    ocp.solver_options.nlp_solver_type = "SQP"
    ocp.solver_options.hessian_approx = "EXACT"
    ocp.solver_options.qp_solver = "PARTIAL_CONDENSING_HPIPM"
    ocp.solver_options.qp_solver_ric_alg = 1
    ocp.solver_options.with_value_sens_wrt_params = True


def export_parametric_ocp(
    param: dict[str, np.ndarray],
    cost_type="EXTERNAL",
    name: str = "point_mass",
    learnable_params: list[str] | None = None,
    N_horizon=20,
    dt=0.01,
) -> AcadosOcp:
    if learnable_params is None:
        learnable_params = []
    ocp = AcadosOcp()

    ocp.model.name = name

    ocp.dims.nx = 4
    ocp.dims.nu = 2

    ocp.model.x = cs.SX.sym("x", ocp.dims.nx)  # type:ignore
    ocp.model.u = cs.SX.sym("u", ocp.dims.nu)  # type:ignore
    ocp.model.xdot = cs.SX.sym("xdot", ocp.dims.nx)  # type:ignore

    ocp.solver_options.N_horizon = N_horizon

    ocp = translate_learnable_param_to_p_global(
        nominal_param=param,
        learnable_param=learnable_params,
        ocp=ocp,
        verbose=True,
    )

    ocp.model.disc_dyn_expr = _disc_dyn_expr(model=ocp.model, dt=dt)

    ocp.cost.cost_type_0 = "EXTERNAL"
    ocp.model.cost_expr_ext_cost_0 = cost_expr_ext_cost_0(ocp.model)

    ocp.cost.cost_type = "EXTERNAL"
    ocp.model.cost_expr_ext_cost = cost_expr_ext_cost(ocp.model)

    ocp.cost.cost_type_e = "EXTERNAL"
    ocp.model.cost_expr_ext_cost_e = cost_expr_ext_cost_e(ocp.model, param)

    ocp.constraints.idxbx = np.array([0, 1, 2, 3])
    ocp.constraints.lbx = np.array([0.0, 0.0, -10.0, -10.0])
    ocp.constraints.ubx = np.array([10, 10, 10.0, 10.0])
    ocp.constraints.x0 = np.array([1.0, 1.0, 0.0, 0.0])

    # Slack both position in both dimensions
    ocp.constraints.idxsbx = np.array([0, 1])
    ocp.cost.zl = np.ones((2,)) * 1e2
    ocp.cost.zu = np.ones((2,)) * 1e2
    ocp.cost.Zl = np.diag([0, 0])
    ocp.cost.Zu = np.diag([0, 0])

    ocp.constraints.idxbu = np.array([0, 1])
    ocp.constraints.lbu = np.array([-5.0, -5.0])
    ocp.constraints.ubu = np.array([+5.0, +5.0])

    if isinstance(ocp.model.p, struct_symSX):
        ocp.model.p = ocp.model.p.cat if ocp.model.p is not None else []
    if isinstance(ocp.model.p_global, struct_symSX):
        ocp.model.p_global = (
            ocp.model.p_global.cat if ocp.model.p_global is not None else None
        )

    return ocp
