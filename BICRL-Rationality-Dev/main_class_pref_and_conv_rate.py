import mdp_utils, mdp_worlds, plot_grid
import bayesian_irl
import copy, IPython, argparse
import numpy as np
import pickle

parser = argparse.ArgumentParser()
parser.add_argument('--nx', type=int, default=10)
parser.add_argument('--ny', type=int, default=8)
parser.add_argument('--N_traj', type=int, default=100)
parser.add_argument('--noise', type=float, default=0.0)
parser.add_argument('--gamma', type=float, default=0.95)
parser.add_argument('--boltz_beta', type=float, default=1)
parser.add_argument('--stdev', type=float, default=1)
parser.add_argument('--num_steps', type=int, default=4000)
parser.add_argument('--iterations', type=int, default=10)
parser.add_argument('--filename', type=str, default='data/')
parser.add_argument('--cnstr_alloc', type=int, default=6)
args = parser.parse_args()


def main():

    nx = args.nx # columns
    ny = args.ny # rows
    N_traj = args.N_traj
    filename = args.filename
    gamma = args.gamma
    noise = args.noise
    boltz_beta = args.boltz_beta
    num_steps = args.num_steps
    iterations = args.iterations
    stdev = args.stdev
    cnstr_alloc = args.cnstr_alloc

    res_dict = {}

    map_constraints_list = []
    map_rew_list = []
    mean_constraints_list = []
    mean_penalty_list = []
    Perf_list = []
    # begin repetition to average out performance of algorithms
    for iteration in range(iterations):
        print('**** Iteration {} **** and cnstr_alloc {}'.format(iteration, cnstr_alloc))
        
        # rewards negative everywhere except for the goal state
        rewards = -1*np.ones(ny * nx)

        # constraints is a binary vector indicating the presence or not of a constraint
        constraints = np.zeros(ny * nx)
        # set some constrains by hand
        # inds = [3*nx, 3*nx+1, 4*nx, 4*nx+1, 3*nx+nx-3, 3*nx+nx-2, 
        # 3*nx+nx-1, 4*nx+nx-3, 4*nx+nx-2, 4*nx+nx-1]
        if cnstr_alloc == 1:
            inds = [3*nx, 3*nx+1, 3*nx+2, 3*nx+3, 3*nx+4, 3*nx+5, 3*nx+6,
            4*nx, 4*nx+1, 4*nx+2, 4*nx+3, 4*nx+4, 4*nx+5, 4*nx+6]
            start_state = nx * (ny - 1)
            terminal_states = [0]
        elif cnstr_alloc == 2:
            inds = [ 2*nx+3, 2*nx+4, 2*nx+5, 2*nx+6, 3*nx+3, 3*nx+4, 3*nx+5, 3*nx+6, 
            4*nx+3, 4*nx+4, 4*nx+5, 4*nx+6,  5*nx+3, 5*nx+4, 5*nx+5, 5*nx+6]
            start_state = nx * (ny - 1) + int(np.floor(nx/2))
            terminal_states = [int(np.floor(nx/2))]
        elif cnstr_alloc == 3:
            inds = [5*nx+5, 5*nx+6, 5*nx+7, 5*nx+8, 5*nx+9,
            2*nx, 2*nx+1, 2*nx+2, 2*nx+3, 2*nx+4]
            start_state = nx * ny - 1
            terminal_states = [0]
        elif cnstr_alloc == 4:
            inds = [4*nx, 4*nx+1, 4*nx+2, 2*nx+4, 1*nx+4, 0*nx+4]
            start_state = nx - 1
            terminal_states = [0]
        elif cnstr_alloc == 5:# change to something
            inds = [3*nx, 3*nx+1, 4*nx, 4*nx+1]
            start_state = nx * (ny - 1)
            terminal_states = [0]
        elif cnstr_alloc == 6:
            inds = [3*nx, 3*nx+1, 3*nx+2, 3*nx+3, 3*nx+4, 3*nx+5,3*nx+6,
            4*nx, 4*nx+1, 4*nx+2, 4*nx+3, 4*nx+4, 4*nx+5, 4*nx+6]
            start_state = nx * (ny - 1)
            terminal_states = [0]



        constraints[inds] = 1
        rewards[terminal_states[0]] = 2
        rewards[inds] = -10
        rewards_fix = - np.ones(ny * nx)
        rewards_fix[terminal_states[0]] = 2
        num_cnstr = len(np.nonzero(constraints)[0])

        env = mdp_worlds.nonrand_gridworld(ny, nx, terminal_states, rewards, constraints, gamma, noise)
        # IPython.embed()
        optimal_policy = mdp_utils.get_optimal_policy(env)

        trajectory_demos = []
        perf_lists = []
        trajectory_demos = []
        for i in range(N_traj):
            trajectory_demos.append(mdp_utils.generate_boltzman_demo(env, boltz_beta, start_state))#
            # trajectory_demos.append(mdp_utils.generate_optimal_demo(env, start_state))
        trajectory_demos = [item for sublist in trajectory_demos for item in sublist]

        # plot_grid.plot_grid(nx, ny, env.state_grid_map, cnstr_alloc, constraints, trajectory_demos)
        # demos = mdp_utils.demonstrate_entire_optimal_policy(env)       
        # save trajectories
        # np.savetxt('traj_demos_' + str(cnstr_alloc) + '.txt' , np.array(trajectory_demos))
        
        # birl = bayesian_irl_rew.BIRL_Rew(env, trajectory_demos, boltz_beta)

        # birl = bayesian_irl_rew.BIRL_Rew(env, trajectory_demos, boltz_beta)
        birl = bayesian_irl.BIRL(env, trajectory_demos, boltz_beta)

        birl.run_mcmc_bern_constraint(num_steps, rewards_fix)
        acc_rate = birl.accept_rate
        print('acceptance rate {}'.format(acc_rate)) 
        mean_constraints, mean_penalty = birl.get_mean_solution(burn_frac=0.2, skip_rate=1)
        # print("mean constraints", mean_constraints)
        map_constraints, map_penalty = birl.get_map_solution()
        
        Perf = birl.Perf_list
        
        map_constraints_list.append(map_constraints)
        map_rew_list.append(map_penalty)
        mean_constraints_list.append(mean_constraints)
        mean_penalty_list.append(mean_penalty)
        Perf_list.append(Perf)
        # print("map constraints", map_constraints)

        # plot_grid.plot_grid_mean_constr(nx, ny, env.state_grid_map, mean_constraints, trajectory_demos)
        # plot_grid.plot_grid(nx, ny, env.state_grid_map, 2, map_constraints, trajectory_demos)        
        # plot_grid.plot_grid_mean_constr(nx, ny, env.state_grid_map, 8, mean_constraints)
        # plot_grid.plot_grid(nx, ny, env.state_grid_map, constraints=map_constraints, trajectories=trajectory_demos)
    # IPython.embed()
    res_dict['MAP'] = [map_constraints_list, map_rew_list]
    res_dict['MEAN'] = [mean_constraints_list, mean_penalty_list]
    res_dict['CLASS'] = Perf_list
    with open(filename + 'Classification_Precision_added_new' + '.pickle', 'wb') as handle:
        pickle.dump(res_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)
    # with open(filename + 'cnstr_alloc' + '_' + str(cnstr_alloc) +  '.pickle', 'wb') as handle:
    #     pickle.dump(res_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)
if __name__=="__main__":
    main()
