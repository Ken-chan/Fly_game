import numpy as np
import random
import tensorflow as tf
import os
import pickle
import time

from collections import deque

class DiscreteDeepQ(object):
    def __init__(self, observation_shape,
                       num_actions,
                       observation_to_actions,
                       optimizer,
                       session,
                       random_action_probability=0.05,
                       exploration_period=500,
                       store_every_nth=4,
                       train_every_nth=4,
                       minibatch_size=100,
                       discount_rate=0.95,
                       max_experience=30000,
                       target_network_update_rate=0.01,
                       summary_writer=None):

        # memorize arguments
        self.observation_shape         = observation_shape
        self.num_actions               = num_actions

        self.q_network                 = observation_to_actions
        self.optimizer                 = optimizer
        self.s                         = session

        self.random_action_probability = random_action_probability
        self.exploration_period        = exploration_period
        self.store_every_nth           = store_every_nth
        self.train_every_nth           = train_every_nth
        self.minibatch_size            = minibatch_size
        self.discount_rate             = tf.constant(discount_rate)
        self.max_experience            = max_experience
        self.target_network_update_rate = \
                tf.constant(target_network_update_rate)

        # deepq state
        self.actions_executed_so_far = 0
        self.experience = deque()

        self.iteration = 0
        self.summary_writer = summary_writer

        self.number_of_times_store_called = 0
        self.number_of_times_train_called = 0

        self.create_variables()

        self.s.run(tf.initialize_all_variables())
        self.s.run(self.target_network_update)

        self.saver = tf.train.Saver()

        self.file = open("nodes.txt", "a")

    def linear_annealing(self, n, total, p_initial, p_final):
        """Linear annealing between p_initial and p_final
        over total steps - computes value at step n"""
        if n >= total:
            return p_final
        else:
            return p_initial - (n * (p_initial - p_final)) / (total)

    def observation_batch_shape(self, batch_size):
        return tuple([batch_size] + list(self.observation_shape))

    def create_variables(self):
        self.target_q_network    = self.q_network.copy(scope="target_network")
        #print(self.target_q_network.variables)

        # FOR REGULAR ACTION SCORE COMPUTATION
        with tf.name_scope("taking_action"):
            self.observation        = tf.placeholder(tf.float32, self.observation_batch_shape(None), name="observation")
            self.action_scores      = tf.identity(self.q_network(self.observation), name="action_scores")
            print(self.action_scores)
            #tf.histogram_summary("action_scores", self.action_scores)
            self.predicted_actions  = tf.argmax(self.action_scores, dimension=1, name="predicted_actions")

        with tf.name_scope("estimating_future_rewards"):
            # FOR PREDICTING TARGET FUTURE REWARDS
            self.next_observation          = tf.placeholder(tf.float32, self.observation_batch_shape(None), name="next_observation")
            self.next_observation_mask     = tf.placeholder(tf.float32, (None,), name="next_observation_mask")
            self.next_action_scores        = tf.stop_gradient(self.target_q_network(self.next_observation))
            #tf.histogram_summary("target_action_scores", self.next_action_scores)
            self.rewards                   = tf.placeholder(tf.float32, (None,), name="rewards")
            target_values                  = tf.reduce_max(self.next_action_scores, reduction_indices=[1,]) * self.next_observation_mask
            self.future_rewards            = self.rewards + self.discount_rate * target_values

        with tf.name_scope("q_value_precition"):
            # FOR PREDICTION ERROR
            self.action_mask                = tf.placeholder(tf.float32, (None, self.num_actions), name="action_mask")
            self.masked_action_scores       = tf.reduce_sum(self.action_scores * self.action_mask, reduction_indices=[1,])
            temp_diff                       = self.masked_action_scores - self.future_rewards
            self.prediction_error           = tf.reduce_mean(tf.square(temp_diff))
            gradients                       = self.optimizer.compute_gradients(self.prediction_error)
            for i, (grad, var) in enumerate(gradients):
                if grad is not None:
                    gradients[i] = (tf.clip_by_norm(grad, 5), var)
            # Add histograms for gradients.
            """for grad, var in gradients:
                tf.histogram_summary(var.name, var)
                if grad is not None:
                    tf.histogram_summary(var.name + '/gradients', grad)"""
            self.train_op                   = self.optimizer.apply_gradients(gradients)

        # UPDATE TARGET NETWORK
        with tf.name_scope("target_network_update"):
            self.target_network_update = []
            for v_source, v_target in zip(self.q_network.variables(), self.target_q_network.variables()):
                # this is equivalent to target = (1-alpha) * target + alpha * source
                update_op = v_target.assign_sub(self.target_network_update_rate * (v_target - v_source))
                self.target_network_update.append(update_op)
                #print("mass =  ", v_source)
            self.target_network_update = tf.group(*self.target_network_update)

        # summaries
        tf.summary.scalar("prediction_error", self.prediction_error)

        self.summarize = tf.summary.merge_all()
        self.no_op1    = tf.no_op()

    def action(self, observation, predicted_action):
        #assert observation.shape == self.observation_shape, \
         #       "Action is performed based on single observation."

        self.actions_executed_so_far += 1
        exploration_p = self.linear_annealing(self.actions_executed_so_far,
                                              self.exploration_period,
                                              1.0,
                                              self.random_action_probability)

        if random.random() < exploration_p:
            return random.randint(0, self.num_actions - 1)
        else:
            self.predicted_actions = tf.argmax(predicted_action, dimension=1, name="predicted_actions")
            #print("neuro_net give prediction")
            with tf.device("/gpu:0"):
                print(self.predicted_actions)
                res = self.s.run(self.predicted_actions, {self.observation: observation[np.newaxis,:]})
                return res[0]

    def exploration_completed(self):
        return min(float(self.actions_executed_so_far) / self.exploration_period, 1.0)

    def store(self, observation, action, reward, newobservation):
        """Store experience, where starting with observation and
        execution action, we arrived at the newobservation and got thetarget_network_update
        reward reward
        If newstate is None, the state/action pair is assumed to be terminal
        """
        if self.number_of_times_store_called % self.store_every_nth == 0:
            self.experience.append((observation, action, reward, newobservation))
            if len(self.experience) > self.max_experience:
                self.experience.popleft()
        self.number_of_times_store_called += 1
        #print(len(self.experience))

    def training_step(self):
        """Pick a self.minibatch_size exeperiences from reply buffer
        and backpropage the value function.
        """
        if self.number_of_times_train_called % self.train_every_nth == 0:
            if len(self.experience) < self.minibatch_size:
                return

            #print(len(self.experience))
            # sample experience.
            samples   = random.sample(range(len(self.experience)), self.minibatch_size)
            samples   = [self.experience[i] for i in samples]

            # bach states
            states         = np.empty(shape=self.observation_batch_shape(len(samples)))
            newstates      = np.empty(self.observation_batch_shape(len(samples)))
            action_mask    = np.zeros((len(samples), self.num_actions))

            newstates_mask = np.empty((len(samples),))
            rewards        = np.empty((len(samples),))

            for i, (state, action, reward, newstate) in enumerate(samples):
                states[i] = state
                action_mask[i] = 0
                action_mask[i][action] = 1
                rewards[i] = reward
                if newstate is not None:
                    newstates[i] = newstate
                    newstates_mask[i] = 1
                else:
                    newstates[i] = 0
                    newstates_mask[i] = 0


            calculate_summaries = self.iteration % 100 == 0 and \
                    self.summary_writer is not None

            with tf.device("/gpu:0"):
                cost, _, summary_str = self.s.run([
                    self.prediction_error,
                    self.train_op,
                    self.summarize if calculate_summaries else self.no_op1, ],
                    {
                    self.observation:            states,
                    self.next_observation:       newstates,
                    self.next_observation_mask:  newstates_mask,
                    self.action_mask:            action_mask,
                    self.rewards:                rewards,
                })
                self.s.run(self.target_network_update)

            self.nodes = ''
            for node in self.q_network.input_layer.Ws[0].eval():
                self.nodes += (str(node)) + "  "
            self.nodes += "\n\n"
            self.file.write(self.nodes)

            if self.number_of_times_train_called % 100 == 0:
                self.save("q_first_model")
                #print(self.q_network.input_layer.Ws[0].eval())
            if calculate_summaries:
                self.summary_writer.add_summary(summary_str, self.iteration)

            self.iteration += 1

        self.number_of_times_train_called += 1

    def save(self, save_dir, debug=False):
        STATE_FILE      = os.path.join(save_dir, 'deepq_state')
        MODEL_FILE      = os.path.join(save_dir, 'model_q')

        # deepq state
        state = {
            'actions_executed_so_far':      self.actions_executed_so_far,
            'iteration':                    self.iteration,
            'number_of_times_store_called': self.number_of_times_store_called,
            'number_of_times_train_called': self.number_of_times_train_called,
        }

        if debug:
            print ('Saving model... ')

        saving_started = time.time()

        self.saver.save(self.s, MODEL_FILE)
        with open(STATE_FILE, "wb") as f:
            pickle.dump(state, f)

        print('done in {} s'.format(time.time() - saving_started))

    def restore(self, save_dir, debug=False):
        # deepq state
        STATE_FILE      = os.path.join(save_dir, 'deepq_state')
        MODEL_FILE      = os.path.join(save_dir, 'model_q')

        with open(STATE_FILE, "rb") as f:
            state = pickle.load(f)
        self.saver.restore(self.s, MODEL_FILE)

        self.actions_executed_so_far      = state['actions_executed_so_far']
        self.iteration                    = state['iteration']
        self.number_of_times_store_called = state['number_of_times_store_called']
        self.number_of_times_train_called = state['number_of_times_train_called']