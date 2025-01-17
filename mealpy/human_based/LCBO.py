#!/usr/bin/env python
# ------------------------------------------------------------------------------------------------------%
# Created by "Thieu Nguyen" at 11:16, 18/03/2020                                                        %
#                                                                                                       %
#       Email:      nguyenthieu2102@gmail.com                                                           %
#       Homepage:   https://www.researchgate.net/profile/Thieu_Nguyen6                                  %
#       Github:     https://github.com/thieu1995                                                        %
#-------------------------------------------------------------------------------------------------------%

from numpy.random import uniform, random, normal, choice
from numpy import array, mean, sqrt, ceil, abs, cos, pi, sin
from copy import deepcopy
from mealpy.optimizer import Root


class OriginalLCBO(Root):
    """
    The original version of: Life Choice-based Optimization (LCBO)
        (A novel life choice-based optimizer)
    Link:
        DOI: https://doi.org/10.1007/s00500-019-04443-z
    """

    def __init__(self, obj_func=None, lb=None, ub=None, verbose=True, epoch=750, pop_size=100, r1=2.35, **kwargs):
        super().__init__(obj_func, lb, ub, verbose, kwargs)
        self.epoch = epoch
        self.pop_size = pop_size
        self.r1 = r1

    def train(self):
        pop = [self.create_solution() for _ in range(self.pop_size)]
        pop, g_best = self.get_sorted_pop_and_global_best_solution(pop, self.ID_FIT, self.ID_MIN_PROB)
        n = int(ceil(sqrt(self.pop_size)))

        # epoch: current chance, self.epoch: number of chances
        for epoch in range(self.epoch):
            for i in range(0, self.pop_size):
                rand_number = random()

                if rand_number > 0.875:  # Update using Eq. 1, update from n best position
                    temp = array([random() * pop[j][self.ID_POS] for j in range(0, n)])
                    temp = mean(temp, axis=0)
                elif rand_number < 0.7:  # Update using Eq. 2-6
                    f1 = 1 - epoch / self.epoch
                    f2 = 1 - f1
                    if i == 0:
                        pop[i] = deepcopy(g_best)
                        continue
                    else:
                        best_diff = f1 * self.r1 * (g_best[self.ID_POS] - pop[i][self.ID_POS])
                        better_diff = f2 * self.r1 * (pop[i-1][self.ID_POS] - pop[i][self.ID_POS])
                    temp = pop[i][self.ID_POS] + random() * better_diff + random() * best_diff
                else:
                    temp = self.ub - (pop[i][self.ID_POS] - self.lb) * random()
                fit = self.get_fitness_position(temp)
                if fit < pop[i][self.ID_FIT]:
                    pop[i] = [temp, fit]

            pop, g_best = self.update_sorted_population_and_global_best_solution(pop, self.ID_MIN_PROB, g_best)
            self.loss_train.append(g_best[self.ID_FIT])
            if self.verbose:
                print(">Epoch: {}, Best fit: {}".format(epoch + 1, g_best[self.ID_FIT]))
        self.solution = g_best
        return g_best[self.ID_POS], g_best[self.ID_FIT], self.loss_train


class BaseLCBO(Root):
    """
    My base version of: Life Choice-based Optimization (LCBO)
        (A novel life choice-based optimizer)
    Link:
        DOI: https://doi.org/10.1007/s00500-019-04443-z
    """

    def __init__(self, obj_func=None, lb=None, ub=None, verbose=True, epoch=750, pop_size=100, r1=2.35, **kwargs):
        super().__init__(obj_func, lb, ub, verbose, kwargs)
        self.epoch = epoch
        self.pop_size = pop_size
        self.r1 = r1

    def train(self):
        pop = [self.create_solution() for _ in range(self.pop_size)]
        pop, g_best = self.get_sorted_pop_and_global_best_solution(pop, self.ID_FIT, self.ID_MIN_PROB)
        n = int(ceil(sqrt(self.pop_size)))

        # epoch: current chance, self.epoch: number of chances
        for epoch in range(self.epoch):
            for i in range(0, self.pop_size):
                rand = random()

                if rand > 0.875:    # Update using Eq. 1, update from n best position
                    temp = array([random() * pop[j][self.ID_POS] for j in range(0, n)])
                    temp = mean(temp, axis=0)
                elif rand < 0.7:    # Update using Eq. 2-6
                    f = (epoch + 1) / self.epoch
                    if i != 0:
                        better_diff = f * self.r1 * (pop[i - 1][self.ID_POS] - pop[i][self.ID_POS])
                    else:
                        better_diff = f * self.r1 * (g_best[self.ID_POS] - pop[i][self.ID_POS])
                    best_diff = (1-f) * self.r1 * (pop[0][self.ID_POS] - pop[i][self.ID_POS])
                    temp = pop[i][self.ID_POS] + uniform() * better_diff + uniform() * best_diff
                else:
                    temp = self.ub - (pop[i][self.ID_POS] - self.lb) * uniform(self.lb, self.ub)
                fit = self.get_fitness_position(temp)
                if fit < pop[i][self.ID_FIT]:
                    pop[i] = [temp, fit]

                ## Batch size idea
                if self.batch_idea:
                    if (i + 1) % self.batch_size == 0:
                        pop, g_best = self.update_sorted_population_and_global_best_solution(pop, self.ID_MIN_PROB, g_best)
                else:
                    if (i + 1) % self.pop_size == 0:
                        pop, g_best = self.update_sorted_population_and_global_best_solution(pop, self.ID_MIN_PROB, g_best)
            self.loss_train.append(g_best[self.ID_FIT])
            if self.verbose:
                print(">Epoch: {}, Best fit: {}".format(epoch + 1, g_best[self.ID_FIT]))
        self.solution = g_best
        return g_best[self.ID_POS], g_best[self.ID_FIT], self.loss_train


class ModifiedLCO(Root):
    """
    The modified version of: Life Choice-Based Optimization (LCBO) based on
        + New ideas and new implementation techniques
        + Levy-flight techniques
        + Linear weight factor
    """

    def __init__(self, obj_func=None, lb=None, ub=None, verbose=True, epoch=750, pop_size=100, **kwargs):
        super().__init__(obj_func, lb, ub, verbose, kwargs)
        self.epoch = epoch
        self.pop_size = pop_size
        self.n1 = int(ceil(sqrt(self.pop_size)))                        # n best position

    def train(self):
        pop = [self.create_solution() for _ in range(self.pop_size)]
        pop, g_best = self.get_sorted_pop_and_global_best_solution(pop, self.ID_FIT, self.ID_MIN_PROB)

        # epoch: current chance, self.epoch: number of chances
        for epoch in range(self.epoch):
            wf = 2 * (1 - epoch / self.epoch)  # weight factor
            for i in range(0, self.pop_size):
                ## Since we already sorted population, we known which ones are 1st group
                rand_number = random()
                if rand_number < 0.1:     # Update solution of best group
                    pos_new = array([random() * pop[j][self.ID_POS] for j in range(0, self.n1)])
                    pos_new = mean(pos_new, axis=0)
                elif 0.1 <= rand_number <= 0.7:  # Exploitation, update group 2
                    if random() < 0.75:
                        pos_new = g_best[self.ID_POS] + wf * normal(0, 1, self.problem_size) * (g_best[self.ID_POS] - pop[i][self.ID_POS])
                    else:
                        pos_new = self.levy_flight(epoch=epoch, position=pop[i][self.ID_POS], g_best_position=g_best[self.ID_POS])
                else:  # Exploration
                    # People in group 3 learning from the current best person and the person slightly better than them,
                    # because they don't have vision
                    pos_new = wf * pop[i][self.ID_POS] +  2 * random() * (g_best[self.ID_POS] - pop[i][self.ID_POS]) + \
                              2 * random() * (pop[i - 1][self.ID_POS] - pop[i][self.ID_POS])
                    fit_new = self.get_fitness_position(pos_new)
                    pos_new_oppo = self.lb + self.ub - g_best[self.ID_POS] + random() * (g_best[self.ID_POS] - pos_new)
                    fit_new_oppo = self.get_fitness_position(pos_new_oppo)
                    if fit_new_oppo < fit_new:
                        pos_new = pos_new_oppo
                fit = self.get_fitness_position(pos_new)
                if fit < pop[i][self.ID_FIT]:
                    pop[i] = [pos_new, fit]

            pop, g_best = self.update_sorted_population_and_global_best_solution(pop, self.ID_MIN_PROB, g_best)
            self.loss_train.append(g_best[self.ID_FIT])
            if self.verbose:
                print(">Epoch: {}, Best fit: {}".format(epoch + 1, g_best[self.ID_FIT]))
        self.solution = g_best
        return g_best[self.ID_POS], g_best[self.ID_FIT], self.loss_train


class ImprovedLCO(Root):
    """
    The improved version of: Life Choice-Based Optimization (LCBO) based on
        + Gaussian distribution
        + Mutation Mechanism
    """

    def __init__(self, obj_func=None, lb=None, ub=None, verbose=True, epoch=750, pop_size=100, **kwargs):
        super().__init__(obj_func, lb, ub, verbose, kwargs)
        self.epoch = epoch
        self.pop_size = pop_size

    def train(self):
        pop = [self.create_solution() for _ in range(self.pop_size)]
        pop, g_best = self.get_sorted_pop_and_global_best_solution(pop, self.ID_FIT, self.ID_MIN_PROB)
        pop_len = int(self.pop_size / 2)
        # epoch: current chance, self.epoch: number of chances
        for epoch in range(self.epoch):
            for i in range(0, self.pop_size):
                rand = random()
                if rand > 0.875:  # Update using Eq. 1, update from n best position
                    n = int(ceil(sqrt(self.pop_size)))
                    pos_new = array([uniform() * pop[j][self.ID_POS] for j in range(0, n)])
                    pos_new = mean(pos_new, axis=0)
                elif rand < 0.7:  # Update using Eq. 2-6
                    f = (epoch + 1) / self.epoch
                    if i != 0:
                        better_diff = f * uniform() * (pop[i - 1][self.ID_POS] - pop[i][self.ID_POS])
                    else:
                        better_diff = f * uniform() * (g_best[self.ID_POS] - pop[i][self.ID_POS])
                    best_diff = (1 - f) * uniform() * (pop[0][self.ID_POS] - pop[i][self.ID_POS])
                    pos_new = pop[i][self.ID_POS] + better_diff + best_diff
                else:
                    pos_new = self.ub - (pop[i][self.ID_POS] - self.lb) * uniform(self.lb, self.ub)
                fit = self.get_fitness_position(pos_new)
                if fit < pop[i][self.ID_FIT]:
                    pop[i] = [pos_new, fit]
                ## Batch size idea
                if self.batch_idea:
                    if (i + 1) % self.batch_size == 0:
                        pop, g_best = self.update_sorted_population_and_global_best_solution(pop, self.ID_MIN_PROB, g_best)
                else:
                    if (i + 1) % self.pop_size == 0:
                        pop, g_best = self.update_sorted_population_and_global_best_solution(pop, self.ID_MIN_PROB, g_best)
            ## Sort the updated population based on fitness
            pop = sorted(pop, key=lambda item: item[self.ID_FIT])
            pop_s1, pop_s2 = pop[:pop_len], pop[pop_len:]

            ## Mutation scheme
            for i in range(0, pop_len):
                pos_new = pop_s1[i][self.ID_POS] * (1 + normal(0, 1, self.problem_size))
                fit = self.get_fitness_position(pos_new)
                if fit < pop_s1[i][self.ID_FIT]:
                    pop_s1[i] = [pos_new, fit]

            ## Search Mechanism
            pos_s1_list = [item[self.ID_POS] for item in pop_s1]
            pos_s1_mean = mean(pos_s1_list, axis=0)
            for i in range(0, pop_len):
                pos_new = (g_best[self.ID_POS] - pos_s1_mean) - random() * (self.lb + random() * (self.ub - self.lb))
                fit = self.get_fitness_position(pos_new)
                pop_s2[i] = [pos_new, fit]

            ## Construct a new population
            pop = pop_s1 + pop_s2
            pop, g_best = self.update_sorted_population_and_global_best_solution(pop, self.ID_MIN_PROB, g_best)

            self.loss_train.append(g_best[self.ID_FIT])
            if self.verbose:
                print(">Epoch: {}, Best fit: {}".format(epoch + 1, g_best[self.ID_FIT]))
        self.solution = g_best
        return g_best[self.ID_POS], g_best[self.ID_FIT], self.loss_train
