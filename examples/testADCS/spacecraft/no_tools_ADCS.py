# -*- coding: utf-8 -*-
"""Simulation module for attitude determination and control system.

This module forms the core of the simulation engine and utilizes the classes
and functions written elsewhere to model the system and perform numerical
integration.
"""

import numpy as np
from scipy.integrate import ode, RK45, odeint
from kinematics import quaternion_derivative
from dynamics import angular_velocity_derivative
from errors import calculate_attitude_error, calculate_attitude_rate_error

import matplotlib.pyplot as plt
from spacecraft import Spacecraft
from actuators import Actuators
from sensors import Gyros, Magnetometer, EarthHorizonSensor
from controller import PDController
from math_utils import (quaternion_multiply, t1_matrix, t2_matrix, t3_matrix,
                        dcm_to_quaternion, quaternion_to_dcm, normalize, cross)
# from simulation import simulate_adcs

# added
import paho.mqtt.client as mqtt
import json
import logging
import csv
from datetime import datetime, timezone, timedelta
from dotenv import dotenv_values
from nost_tools.application_utils import ConnectionConfig, ShutDownObserver
from nost_tools.entity import Entity
# from nost_tools.observer import Observer
from nost_tools.managed_application import ManagedApplication
from nost_tools.publisher import WallclockTimeIntervalPublisher
from constellation_config_files.config import (
    PREFIX,
    NAME,
    SCALE,
    # TLES,
)

# Define 6U CubeSat mass, dimensions, inertia tensor
sc_mass = 8
sc_dim = [226.3e-3, 100.0e-3, 366.0e-3]
J = 1 / 12 * sc_mass * np.diag([
    sc_dim[1]**2 + sc_dim[2]**2, sc_dim[0]**2 + sc_dim[2]**2,
    sc_dim[0]**2 + sc_dim[1]**2
])
# sc_dipole = np.array([0, 0.018, 0])

# Define  `PDController` object
controller = PDController(
    k_d=np.diag([.01, .01, .01]), k_p=np.diag([.1, .1, .1]))

perfect_gyros = Gyros(bias_stability=0, angular_random_walk=0)

perfect_magnetometer = Magnetometer(resolution=0)

perfect_earth_horizon_sensor = EarthHorizonSensor(accuracy=0)

perfect_actuators = Actuators(
    rxwl_mass=226e-3,
    rxwl_radius=0.5 * 65e-3,
    rxwl_max_torque=np.inf,
    rxwl_max_momentum=np.inf,
    noise_factor=0.0)

# define some orbital parameters
mu_earth = 3.986004418e14
R_e = 6.3781e6
orbit_radius = R_e + 400e3
orbit_w = np.sqrt(mu_earth / orbit_radius**3)
period = 2 * np.pi / orbit_w

# define a function that returns the inertial position and velocity of the
# spacecraft (in m & m/s) at any given time
def position_velocity_func(t):
    r = orbit_radius / np.sqrt(2) * np.array([
        -np.cos(orbit_w * t),
        np.sqrt(2) * np.sin(orbit_w * t),
        np.cos(orbit_w * t),
    ])
    v = orbit_w * orbit_radius / np.sqrt(2) * np.array([
        np.sin(orbit_w * t),
        np.sqrt(2) * np.cos(orbit_w * t),
        -np.sin(orbit_w * t),
    ])
    return r, v

# compute the initial inertial position and velocity
r_0, v_0 = position_velocity_func(0)

# define the body axes in relation to where we want them to be:
# x = Earth-pointing
# y = pointing along the velocity vector
# z = normal to the orbital plane
b_x = -normalize(r_0)
b_y = normalize(v_0)
b_z = cross(b_x, b_y)

# construct the nominal DCM from inertial to body (at time 0) from the body
# axes and compute the equivalent quaternion
dcm_0_nominal = np.stack([b_x, b_y, b_z])
dcm_target = dcm_0_nominal
q_0_nominal = dcm_to_quaternion(dcm_0_nominal)

# compute the nominal angular velocity required to achieve the reference
# attitude; first in inertial coordinates then body
w_nominal_i = 2 * np.pi / period * normalize(cross(r_0, v_0))
w_nominal = np.matmul(dcm_0_nominal, w_nominal_i)

# provide some initial offset in both the attitude and angular velocity
q_0 = q_0_nominal
w_0 = w_nominal
# q_0 = quaternion_multiply(
#     np.array(
#         [0, np.sin(45 * np.pi / 180 / 2), 0,
#           np.cos(45 * np.pi / 180 / 2)]), q_0_nominal)
# w_0 = w_nominal + np.array([0.005, 0, 0])

# define a function that will model perturbations
def perturbations_func(satellite):
    return (satellite.approximate_gravity_gradient_torque() +
            satellite.approximate_magnetic_field_torque())

# define a function that returns the desired state at any given point in
# time (the initial state and a subsequent rotation about the body x, y, or
# z axis depending upon which nominal angular velocity term is nonzero)
def desired_state_func(t):
    if w_nominal[0] != 0:
        dcm_nominal = np.matmul(t1_matrix(w_nominal[0] * t), dcm_target)
    elif w_nominal[1] != 0:
        dcm_nominal = np.matmul(t2_matrix(w_nominal[1] * t), dcm_target)
    elif w_nominal[2] != 0:
        dcm_nominal = np.matmul(t3_matrix(w_nominal[2] * t), dcm_target)
    return dcm_nominal, w_nominal

satellite = Spacecraft(
    J=J,
    controller=controller,
    gyros=perfect_gyros,
    magnetometer=perfect_magnetometer,
    earth_horizon_sensor=perfect_earth_horizon_sensor,
    actuators=perfect_actuators,
    q=q_0,
    w=w_0,
    r=r_0,
    v=v_0)


def derivatives_func(t, x, satellite, desired_state_func, perturbations_func,
                     position_velocity_func, delta_t):
    """Computes the derivative of the spacecraft state
    
    Args:
        t (float): the time (in seconds)
        x (numpy ndarray): the state (10x1) where the elements are:
            [0, 1, 2, 3]: the quaternion describing the spacecraft attitude
            [4, 5, 6]: the angular velocity of the spacecraft
            [7, 8, 9]: the angular velocities of the reaction wheels
        satellite (Spacecraft): the Spacecraft object that represents the
            satellite being modeled
        desired_state_func (function): the function that should compute the
            nominal attitude (in DCM form) and angular velocity; its header
            must be (t)
        perturbations_func (function): the function that should compute the
            perturbation torques (N * m); its header must be (satellite)
        position_velocity_func (function): the function that should compute
            the position and velocity; its header must be (t)
        delta_t (float): the time between user-defined integrator steps
                (not the internal/adaptive integrator steps) in seconds
    
    Returns:
        numpy ndarray: the derivative of the state (10x1) with respect to time
    """
    r, v = position_velocity_func(t)
    satellite.q = normalize(x[0:4])
    satellite.w = x[4:7]
    satellite.r = r
    satellite.v = v
    # only set if the satellite has actuators
    try:
        satellite.actuators.w_rxwls = x[7:10]
    except AttributeError:
        pass
    M_applied, w_dot_rxwls, _ = simulate_estimation_and_control(
        t, satellite, desired_state_func, delta_t)

    # calculate the perturbing torques on the satellite
    M_perturb = perturbations_func(satellite)

    dx = np.empty((10, ))
    dx[0:4] = quaternion_derivative(satellite.q, satellite.w)
    dx[4:7] = angular_velocity_derivative(satellite.J, satellite.w,
                                          [M_applied])
    dx[7:10] = w_dot_rxwls
    return dx


def simulate_estimation_and_control(t,
                                    satellite,
                                    desired_state_func,
                                    delta_t,
                                    log=True):
    """Simulates attitude estimation and control for derivatives calculation
    
    Args:
        t (float): the time (in seconds)
        satellite (Spacecraft): the Spacecraft object that represents the
            satellite being modeled
        desired_state_func (function): the function that should compute the
            nominal attitude (in DCM form) and angular velocity; its header
            must be (t)
        perturbations_func (function): the function that should compute the
            perturbation torques (N * m); its header must be (t, q, w)
        delta_t (float): the time between user-defined integrator steps
                (not the internal/adaptive integrator steps) in seconds
    
    Returns:
        numpy ndarray: the control moment (3x1) as actually applied on
                the reaction wheels (the input control torque with some
                Gaussian noise applied) (N * m)
        numpy ndarray: the angular acceleration of the 3 reaction wheels
            applied to achieve the applied torque (rad/s^2)
        dict: a dictionary containing results logged for this simulation step;
            Contains:
                - DCM_estimated (numpy ndarray): estimated DCM
                - w_estimated (numpy ndarray): estimated angular velocity
                - DCM_desired (numpy ndarray): desired DCM
                - w_desired (numpy ndarray): desired angular velocity
                - attitude_err (numpy ndarray): attitude error
                - attitude_rate_err (numpy ndarray): attitude rate error
                - M_ctrl (numpy ndarray): control torque
                - M_applied (numpy ndarray): applied control torque
                - w_dot_rxwls (numpy ndarray): angular acceleration of
                    reaction wheels
    """
    # get an attitude and angular velocity estimate from the sensors
    w_estimated = satellite.estimate_angular_velocity(t, delta_t)
    DCM_estimated = satellite.estimate_attitude(t, delta_t)

    # compute the desired attitude and angular velocity
    DCM_desired, w_desired = desired_state_func(t)

    # calculate the errors between your desired and estimated state
    attitude_err = calculate_attitude_error(DCM_desired, DCM_estimated)
    attitude_rate_err = calculate_attitude_rate_error(w_desired, w_estimated,
                                                      attitude_err)

    # determine the control torques necessary to change state
    M_ctrl = satellite.calculate_control_torques(attitude_err,
                                                 attitude_rate_err)

    # use actuators to apply the control torques
    M_applied, w_dot_rxwls = satellite.apply_control_torques(
        M_ctrl, t, delta_t)

    if log:
        logged_results = {
            "DCM_estimated": DCM_estimated,
            "w_estimated": w_estimated,
            "DCM_desired": DCM_desired,
            "w_desired": w_desired,
            "attitude_err": attitude_err,
            "attitude_rate_err": attitude_rate_err,
            "M_ctrl": M_ctrl,
            "M_applied": M_applied,
            "w_dot_rxwls": w_dot_rxwls
        }
    else:
        logged_results = None

    return M_applied, w_dot_rxwls, logged_results

def run_adcs(mqttc, obj, msg):
    """ Callback that parses message and runs one ADCS step """
    
    message = json.loads(msg.payload.decode("utf-8"))
    i = message["i"]
    t = message["t"]
    dcm_target = message["dcm_target"]
    dcm_target = np.array(dcm_target)
    
    def desired_state_func(t):
        if w_nominal[0] != 0:
            dcm_nominal = np.matmul(t1_matrix(w_nominal[0] * t), dcm_target)
        elif w_nominal[1] != 0:
            dcm_nominal = np.matmul(t2_matrix(w_nominal[1] * t), dcm_target)
        elif w_nominal[2] != 0:
            dcm_nominal = np.matmul(t3_matrix(w_nominal[2] * t), dcm_target)
        return dcm_nominal, w_nominal

    
    # if verbose:
    #     print("Starting propagation at time: {}".format(t))
    
    if solver.successful() and t <= stop_time:
        # if verbose:
        #     print("Time: {}\nState: {}\n".format(t, solver.y))
            
        # this section currently duplicates calculations for logging purposes
        q = normalize(solver.y[0:4])
        w = solver.y[4:7]
        r, v = position_velocity_func(t)
        satellite.q = q
        satellite.w = w
        satellite.r = r
        satellite.v = v
        _, _, log = simulate_estimation_and_control(
            t, satellite, desired_state_func, delta_t, log=True)
        times[i] = t
        q_actual[i] = q
        w_actual[i] = w
        w_rxwls[i] = solver.y[7:10]
        DCM_estimated[i] = log["DCM_estimated"]
        w_estimated[i] = log["w_estimated"]
        DCM_desired[i] = log["DCM_desired"]
        w_desired[i] = log["w_desired"]
        attitude_err[i] = log["attitude_err"]
        attitude_rate_err[i] = log["attitude_rate_err"]
        M_ctrl[i] = log["M_ctrl"]
        M_applied[i] = log["M_applied"]
        w_dot_rxwls[i] = log["w_dot_rxwls"]
        M_perturb[i] = perturbations_func(satellite)
        positions[i] = r
        velocities[i] = v
        # print("t=",t,dcm_target)

        # desired_state_func(t)
        solver.set_f_params(satellite, desired_state_func, perturbations_func,
                    position_velocity_func, delta_t)

        print("t=",t,desired_state_func(t))
        # continue integrating      
        solver.integrate(t + delta_t)
    
    
    results = {}
    results["times"] = times[:-1]
    results["q_actual"] = q_actual[:-1]
    results["w_actual"] = w_actual[:-1]
    results["w_rxwls"] = w_rxwls[:-1]
    results["DCM_estimated"] = DCM_estimated[:-1]
    results["w_estimated"] = w_estimated[:-1]
    results["DCM_desired"] = DCM_desired[:-1]
    results["w_desired"] = w_desired[:-1]
    results["attitude_err"] = attitude_err[:-1]
    results["attitude_rate_err"] = attitude_rate_err[:-1]
    results["M_ctrl"] = M_ctrl[:-1]
    results["M_applied"] = M_applied[:-1]
    results["M_perturb"] = M_perturb[:-1]
    #return results
    
    #plot the desired results (logged at each delta_t)
    plot = False
    if plot == True:
        tag=r"(Perfect Estimation \& Control)"
        plt.figure(1)
        plt.subplot(411)
        # plt.title(r"Evolution of Quaternion Components over Time")
        plt.plot(results["times"], results["q_actual"][:, 0])
        plt.ylabel(r"$Q_0$")
        plt.subplot(412)
        plt.plot(results["times"], results["q_actual"][:, 1])
        plt.ylabel(r"$Q_1$")
        plt.subplot(413)
        plt.plot(results["times"], results["q_actual"][:, 2])
        plt.ylabel(r"$Q_2$")
        plt.subplot(414)
        plt.plot(results["times"], results["q_actual"][:, 3])
        plt.ylabel(r"$Q_3$")
        plt.xlabel(r"Time (s)")
        plt.subplots_adjust(
            left=0.08, right=0.94, bottom=0.08, top=0.94, hspace=0.3)
        
        plt.figure(2)
        plt.subplot(311)
        plt.title(r"Evolution of Angular Velocity over Time {}".format(tag))
        plt.plot(results["times"], results["w_actual"][:, 0], label="actual")
        plt.plot(
            results["times"],
            results["w_desired"][:, 0],
            label="desired",
            linestyle="--")
        plt.ylabel(r"$\omega_x$ (rad/s)")
        plt.legend()
        plt.subplot(312)
        plt.plot(results["times"], results["w_actual"][:, 1], label="actual")
        plt.plot(
            results["times"],
            results["w_desired"][:, 1],
            label="desired",
            linestyle="--")
        plt.ylabel(r"$\omega_y$ (rad/s)")
        plt.legend()
        plt.subplot(313)
        plt.plot(results["times"], results["w_actual"][:, 2], label="actual")
        plt.plot(
            results["times"],
            results["w_desired"][:, 2],
            label="desired",
            linestyle="--")
        plt.ylabel(r"$\omega_z$ (rad/s)")
        plt.xlabel(r"Time (s)")
        plt.legend()
        plt.subplots_adjust(
            left=0.08, right=0.94, bottom=0.08, top=0.94, hspace=0.3)
        
        plt.figure(3)
        plt.subplot(311)
        plt.title(r"Angular Velocity of Reaction Wheels over Time {}".format(tag))
        plt.plot(results["times"], results["w_rxwls"][:, 0])
        plt.ylabel(r"$\omega_1$ (rad/s)")
        plt.subplot(312)
        plt.plot(results["times"], results["w_rxwls"][:, 1])
        plt.ylabel(r"$\omega_2$ (rad/s)")
        plt.subplot(313)
        plt.plot(results["times"], results["w_rxwls"][:, 2])
        plt.ylabel(r"$\omega_3$ (rad/s)")
        plt.xlabel(r"Time (s)")
        plt.subplots_adjust(
            left=0.08, right=0.94, bottom=0.08, top=0.94, hspace=0.3)
        
        plt.figure(4)
        plt.subplot(311)
        plt.title(r"Perturbation Torques over Time {}".format(tag))
        plt.plot(results["times"], results["M_perturb"][:, 0])
        plt.ylabel(r"$M_x (N \cdot m)$")
        plt.subplot(312)
        plt.plot(results["times"], results["M_perturb"][:, 1])
        plt.ylabel(r"$M_y (N \cdot m)$")
        plt.subplot(313)
        plt.plot(results["times"], results["M_perturb"][:, 2])
        plt.ylabel(r"$M_z (N \cdot m)$")
        plt.xlabel(r"Time (s)")
        plt.subplots_adjust(
            left=0.08, right=0.94, bottom=0.08, top=0.94, hspace=0.3)
        
        plt.figure(5)
        DCM_actual = np.empty(results["DCM_desired"].shape)
        for i, q in enumerate(results["q_actual"]):
            DCM_actual[i] = quaternion_to_dcm(q)
        
        k = 1
        for i in range(3):
            for j in range(3):
                plot_num = int("33{}".format(k))
                plt.subplot(plot_num)
                if k == 2:
                    plt.title(
                        r"Evolution of DCM Components over Time {}".format(tag))
                plt.plot(results["times"], DCM_actual[:, i, j], label="actual")
                plt.plot(
                    results["times"],
                    results["DCM_desired"][:, i, j],
                    label="desired",
                    linestyle="--")
                element = "T_{" + str(i + 1) + str(j + 1) + "}"
                plt.ylabel("$" + element + "$")
                if k >= 7:
                    plt.xlabel(r"Time (s)")
                plt.legend()
                k += 1
        plt.subplots_adjust(
            left=0.08, right=0.94, bottom=0.08, top=0.94, hspace=0.25, wspace=0.3)
        
        plt.figure(6)
        k = 1
        for i in range(3):
            for j in range(3):
                plot_num = int("33{}".format(k))
                plt.subplot(plot_num)
                if k == 2:
                    plt.title(
                        r"Actual vs Estimated Attitude over Time {}".format(tag))
                plt.plot(results["times"], DCM_actual[:, i, j], label="actual")
                plt.plot(
                    results["times"],
                    results["DCM_estimated"][:, i, j],
                    label="estimated",
                    linestyle="--",
                    color="y")
                element = "T_{" + str(i + 1) + str(j + 1) + "}"
                plt.ylabel("$" + element + "$")
                if k >= 7:
                    plt.xlabel(r"Time (s)")
                plt.legend()
                k += 1
        plt.subplots_adjust(
            left=0.08, right=0.94, bottom=0.08, top=0.94, hspace=0.25, wspace=0.3)
        
        plt.figure(7)
        plt.subplot(311)
        plt.title(r"Actual vs Estimated Angular Velocity over Time {}".format(tag))
        plt.plot(results["times"], results["w_actual"][:, 0], label="actual")
        plt.plot(
            results["times"],
            results["w_estimated"][:, 0],
            label="estimated",
            linestyle="--",
            color="y")
        plt.ylabel(r"$\omega_x$ (rad/s)")
        plt.legend()
        plt.subplot(312)
        plt.plot(results["times"], results["w_actual"][:, 1], label="actual")
        plt.plot(
            results["times"],
            results["w_estimated"][:, 1],
            label="estimated",
            linestyle="--",
            color="y")
        plt.ylabel(r"$\omega_y$ (rad/s)")
        plt.legend()
        plt.subplot(313)
        plt.plot(results["times"], results["w_actual"][:, 2], label="actual")
        plt.plot(
            results["times"],
            results["w_estimated"][:, 2],
            label="estimated",
            linestyle="--",
            color="y")
        plt.ylabel(r"$\omega_z$ (rad/s)")
        plt.xlabel(r"Time (s)")
        plt.legend()
        plt.subplots_adjust(
            left=0.08, right=0.94, bottom=0.08, top=0.94, hspace=0.3)
        
        plt.figure(8)
        plt.subplot(311)
        plt.title(r"Commanded vs Applied Torques over Time {}".format(tag))
        plt.plot(results["times"], results["M_applied"][:, 0], label="applied")
        plt.plot(
            results["times"],
            results["M_ctrl"][:, 0],
            label="commanded",
            linestyle="--")
        plt.ylabel(r"$M_x (N \cdot m)$")
        plt.legend()
        plt.subplot(312)
        plt.plot(results["times"], results["M_applied"][:, 1], label="applied")
        plt.plot(
            results["times"],
            results["M_ctrl"][:, 1],
            label="commanded",
            linestyle="--")
        plt.ylabel(r"$M_y (N \cdot m)$")
        plt.legend()
        plt.subplot(313)
        plt.plot(results["times"], results["M_applied"][:, 2], label="applied")
        plt.plot(
            results["times"],
            results["M_ctrl"][:, 2],
            label="commanded",
            linestyle="--")
        plt.ylabel(r"$M_z (N \cdot m)$")
        plt.xlabel(r"Time (s)")
        plt.legend()
        plt.subplots_adjust(
            left=0.08, right=0.94, bottom=0.08, top=0.94, hspace=0.3)
        
        plt.show()


# name guard used to ensure script only executes if it is run as the __main__
if __name__ == "__main__":
    start_time=0
    delta_t=1
    stop_time=6001
    verbose=True
    i = 0

    try:
        init_state = [*satellite.q, *satellite.w, *satellite.actuators.w_rxwls]
    except AttributeError:
        init_state = [*satellite.q, *satellite.w, 0, 0, 0]

    solver = ode(derivatives_func)
    solver.set_integrator(
        'lsoda',
        rtol=(1e-10, 1e-10, 1e-10, 1e-10, 1e-10, 1e-10, 1e-10, 1e-6, 1e-6,
              1e-6),
        atol=(1e-12, 1e-12, 1e-12, 1e-12, 1e-12, 1e-12, 1e-12, 1e-8, 1e-8,
              1e-8),
        nsteps=10000)
    solver.set_initial_value(y=init_state, t=start_time)
    solver.set_f_params(satellite, desired_state_func, perturbations_func,
                        position_velocity_func, delta_t)

    length = int((stop_time - 0) / delta_t + 1)
    times = np.empty((length, ))
    q_actual = np.empty((length, 4))
    w_actual = np.empty((length, 3))
    w_rxwls = np.empty((length, 3))
    DCM_estimated = np.empty((length, 3, 3))
    w_estimated = np.empty((length, 3))
    DCM_desired = np.empty((length, 3, 3))
    w_desired = np.empty((length, 3))
    attitude_err = np.empty((length, 3))
    attitude_rate_err = np.empty((length, 3))
    M_ctrl = np.empty((length, 3))
    M_applied = np.empty((length, 3))
    w_dot_rxwls = np.empty((length, 3))
    M_perturb = np.empty((length, 3))
    positions = np.empty((length, 3))
    velocities = np.empty((length, 3))


    # Note that these are loaded from a .env file in current working directory
    credentials = dotenv_values(".env")
    HOST, PORT = credentials["HOST"], int(credentials["PORT"])
    USERNAME, PASSWORD = credentials["USERNAME"], credentials["PASSWORD"]
    # build the MQTT client
    client = mqtt.Client()
    # set client username and password
    client.username_pw_set(username=USERNAME, password=PASSWORD)
    # set tls certificate
    client.tls_set()
    # connect to MQTT server
    client.connect(HOST, PORT)
    # subscribe to science event topics
    client.subscribe("BCtest/ADCS/heartbeat",0)
    # bind the message handler
    client.on_message = run_adcs
    # start a background thread to let MQTT do things
    client.loop_start()

    # # add message callbacks
    # app.add_message_callback("manager", "status", simulate)