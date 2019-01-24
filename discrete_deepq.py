import numpy as np
import random
import tensorflow as tf
from keras.models import Sequential
from keras.layers import Dense
from keras.models import load_model
import keras

from collections import deque

class DiscreteDeepQ(object):
    def __init__(self, observation_shape,
                       act_size, acts,
                       random_action_probability=0.15,
                       exploration_period=1000,
                       store_every_nth=4,
                       train_every_nth=4,
                       minibatch_size=32,
                       discount_rate=0.95,
                       max_experience=30000,
                       target_network_update_rate=10000,
                       learning_rate=0.01, decay=0.95, save_path=None):

        # memorize arguments
        self.acts = acts
        self.observation_size         = observation_shape
        self.act_size               = act_size
        self.save_path = save_path

        self.random_action_probability = random_action_probability
        self.exploration_period        = exploration_period
        self.store_every_nth           = store_every_nth
        self.train_every_nth           = train_every_nth
        self.minibatch_size            = minibatch_size
        self.discount_rate             = tf.constant(discount_rate)
        self.max_experience            = max_experience
        self.learning_rate = learning_rate
        self.gamma = decay
        self.update_target_network_every = target_network_update_rate

        # deepq state
        self.actions_executed_so_far = 0
        self.experience = deque()

        self.iteration = 0
        self.number_of_times_store_called = 0
        self.number_of_times_train_called = 0

        self.opt = keras.optimizers.RMSprop(lr=self.learning_rate, rho=0.9, decay=self.gamma)
        self.model = Sequential()
        self.model.add(Dense(50, input_dim=(self.observation_size+self.act_size), activation='relu'))
        #self.model.add(Dense(32, activation='relu'))
        self.model.add(Dense(1, activation='linear'))

        #self.model.summary()
        self.model.compile(loss="mean_squared_error", optimizer=self.opt)

        self.target_model = keras.models.clone_model(self.model)
        self.target_model.set_weights(self.model.get_weights())
        self.target_model.compile(loss="mean_squared_error", optimizer=self.opt)

    def linear_annealing(self, n, total, p_initial, p_final):
        """Linear annealing between p_initial and p_final
        over total steps - computes value at step n"""
        if n >= total:
            return p_final
        else:
            return p_initial - (n * (p_initial - p_final)) / (total)


    #def test(self):

    def action(self, new_observation):
        #print(self.actions_executed_so_far)
        self.actions_executed_so_far += 1
        exploration_p = self.linear_annealing(self.actions_executed_so_far,
                                              self.exploration_period,
                                              1.0,
                                              self.random_action_probability)
        if random.random() < exploration_p:
            self._action = random.randint(0, len(self.acts) - 1)
            return self._action
        else:
            #print("neuro_net give prediction")
            self.i = 0
            self._action = 0
            self.q = -1000000
            for act in self.acts:
                X = np.array(np.concatenate((new_observation, act), axis=None)).reshape(1, self.observation_size+self.act_size)
                #print("odin ",X.shape)
                self.predicted_q = self.model.predict(X)

                print(self.predicted_q)
                if self.predicted_q > self.q:
                    self._action = self.i
                    self.q = self.predicted_q
                self.i += 1
            print(self._action)
            return self._action


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

            # sample experience.
            samples   = random.sample(range(len(self.experience)), self.minibatch_size)
            samples   = [self.experience[i] for i in samples]


            self.X = np.zeros((self.minibatch_size, self.observation_size + self.act_size))
            self.Y = np.zeros((self.minibatch_size, 1))
            for i, (state, action, reward, newstate) in enumerate(samples):
                self.X[i] = np.array(np.concatenate((state, action)))
                #print("dwa ", self.X[i].shape)
                self.Q_active = self.model.predict(self.X[i].reshape(1, self.observation_size+self.act_size))
                self.j = 0
                self.q = -1000000
                for act in self.acts:
                    X = np.concatenate((newstate, act)).reshape(1, self.observation_size+self.act_size)
                    self.predicted_q = self.target_model.predict(X)
                    if self.predicted_q > self.q:
                        self.q = self.predicted_q
                    self.j += 1
                self.Q_target = self.q
                self.Y[i] = self.Q_active + self.learning_rate * \
                            (reward + self.gamma * self.Q_target - self.Q_active)

            self.model.fit(self.X, self.Y, epochs=1, batch_size=self.minibatch_size, verbose=0)

            if self.number_of_times_train_called % 1000 == 0:
                self.save(self.save_path)

                #print(self.q_network.input_layer.Ws[0].eval())

            self.iteration += 1

        self.number_of_times_train_called += 1

        if self.number_of_times_train_called % self.update_target_network_every == 0:
            self.target_model = keras.models.clone_model(self.model)
            self.target_model.set_weights(self.model.get_weights())
            self.target_model.compile(loss="mean_squared_error", optimizer=self.opt)
            print("target model updated")

    def save(self, save_dir):
        self.model.save(save_dir)  # creates a HDF5 file
        self.target_model.save('target_model')
        print("model saved")
        #del self.model  # deletes the existing model


    def restore(self, save_dir):
        self.model = load_model(save_dir)
        self.target_model = load_model('target_model')

        """self.model.compile(loss="mean_squared_error", optimizer=self.opt)

        self.target_model.compile(loss="mean_squared_error", optimizer=self.opt)"""
