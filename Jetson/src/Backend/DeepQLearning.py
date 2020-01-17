"""
    This file is the AI functionalilty.

    Simulates the the enviorment of foosball as for the keeper. 
    This simulation has the intention to train an AI to play the game.

    Use the W,A,S,D keys to move the keeper.
    Press C to start the simulation.

    File:
        DeepQLearning.py
    Date:
        16-1-2020
    Version:
        1.1
    Modifier:
        Daniël Boon
        Kelvin Sweere (deels docstrings)
    Used_IDE:
        Visual Studio Code (Python 3.6.7 64-bit)
    Schematic:
        Lucidchart: NLE/AI/LLD AI
    Version management:
        1.0:
            Headers up-to-date.
        1.1:
            Docstrings aangepast naar Google-format. 
"""

import tensorflow as tf      # Deep Learning library
import numpy as np           # Handle matrices

import random                # Handling random number generation
import time                  # Handling time calculation

from collections import deque# Ordered collection with ends
import matplotlib.pyplot as plt # Display graphs
from datetime import datetime


import warnings # This ignore all the warning messages that are normally printed during the training because of skiimage
warnings.filterwarnings('ignore') 

class DQLBase:
    def __init__(self, debug=False):
        self.possible_actions = create_environment()

        self.stack_size = 4 # We stack 4 frames

        # Initialize deque with zero-images one array for each image
        self.stacked_states = deque([np.zeros(4, dtype=np.float) for i in range(self.stack_size)], maxlen=4) 

        ### MODEL HYPERPARAMETERS
        # Our input is a stack of 4 frames hence 84x84x4 (Width, height, channels)
        state_size = [4, 4]
        action_size = 4  # game.get_available_buttons_size()              # 3 possible actions: left, right, shoot
        #TODO: was 0.0002
        learning_rate = 0.01      # Alpha (aka learning rate)

        ### TRAINING HYPERPARAMETERS
        total_episodes = 500        # Total episodes for training
        self.max_steps = 1000              # Max possible steps in an episode
        #TODO: was 64
        self.batch_size = 32

        # Exploration parameters for epsilon greedy strategy
        #TODO: explore_start was 1.0
        self.explore_start = 1.0            # exploration probability at start
        self.explore_stop = 0.01            # minimum exploration probability
        self.decay_rate = 0.0001            # exponential decay rate for exploration prob

        # Q learning hyperparameters
        self.gamma = 0.95               # Discounting rate

        ### MEMORY HYPERPARAMETERS
        # Number of experiences stored in the Memory when initialized for the first time
        pretrain_length = self.batch_size
        memory_size = 10000          # Number of experiences the Memory can keep
       
        ### MODIFY THIS TO FALSE IF YOU JUST WANT TO SEE THE TRAINED AGENT
        training = True

        ## TURN THIS TO TRUE IF YOU WANT TO RENDER THE ENVIRONMENT
        episode_render = False

        # Reset the graph
        tf.reset_default_graph()

        # Instantiate the DQNetwork
        self.DQNetwork = DQNetwork(state_size, action_size, learning_rate)
        
        # Instantiate memory
        self.memory = Memory(max_size = memory_size)

        # Setup TensorBoard Writer
        self.writer = tf.summary.FileWriter("/tensorboard/dqn/1")

        ## Losses
        tf.summary.scalar("Loss", self.DQNetwork.loss)

        self.write_op = tf.summary.merge_all()

        # Saver will help us to save our model
        self.saver = tf.train.Saver()

        #with tf.Session() as self.sess:
        self.sess = tf.Session()
        # Initialize the variables
        self.sess.run(tf.global_variables_initializer())
        
        # Initialize the decay rate (that will use to reduce epsilon) 
        self.decay_step = 0
                    # Set step to 0
        self.step = 0
        
        # Initialize the rewards of the episode
        self.episode_rewards = []

        # Make a new episode and observe the first state
        #game.new_episode()
        self.state = np.array([0, 0, 0, 0])
        
        # Remember that stack frame function also call our preprocess function.
        self.state, self.stacked_states = stack_states(self.stacked_states, self.state, True, self.stack_size)
        self.goals_old = 0
        self.blocks_old = 0
        self.vel_x_old = 0
        self.vel_y_old = 0
        self.reward = 0
        self.total_reward = []
        self.episode = 0
        self.action = 0
        self.vel_x = 0
        self.vel_y = 0
    
    def get_ai_action(self):
        
        for i in range(len(self.state[0])-1):
            self.vel_x = self.state[0][i+1] - self.state[0][i]
            self.vel_y = self.state[1][i+1] - self.state[1][i]

        target = self.state[1][0]+(((-15-self.state[0][0])/self.vel_x) * self.vel_y)

        if((self.vel_x > 0) or (target > 11.26) or (target < 6.16)):
            target = np.nan


        # print(target)

        done = 0
        old_action = self.action

        action, explore_probability = predict_action(self.explore_start, self.explore_stop, self.decay_rate, self.decay_step, self.state, self.possible_actions, self.sess, self.DQNetwork)
        self.action = action
        if (not np.isnan(target)):
            if (np.array_equal(action, self.possible_actions[0])):
                if(target > self.state[3][0]):
                    self.reward += 0.2*abs(self.state[3][0]-target)
                else:
                    self.reward -= 0.05*(5.1-abs(self.state[3][0]-target))
            elif np.array_equal(action, self.possible_actions[1]):
                if(target < self.state[3][0]):
                    self.reward += 0.2*abs(self.state[3][0]-target)
                else:
                    self.reward -= 0.05*(5.1-abs(self.state[3][0]-target))

        if np.array_equal(action, self.possible_actions[2]):

            if( (self.state[0][0] > -16) and (self.state[0][0] < -14) and (abs(self.state[3][0]-self.state[1][0]) < 0.37)):
                self.reward += 0.5
            else:
                self.reward -= 0.1
        
        if np.array_equal(action, self.possible_actions[3]):
            if(np.isnan(target)):
                self.reward += 0.01
            elif(abs(self.state[1][0]-target) < 0.37):
                self.reward += 0.3
            else:
                self.reward -= 0.05



        return action, old_action, target, self.vel_x, self.vel_x_old

    def update_data(self, done, ball, keeper):
        if(not done):
            self.episode_rewards.append(self.reward)
            # Get the next state
            next_state =  np.array([ball.position.x, ball.position.y, keeper.position.x, keeper.position.y])
            
            # Stack the frame of the next_state
            next_state, self.stacked_states = stack_states(self.stacked_states, next_state, False, self.stack_size)
            

            # Add experience to memory
            self.memory.add((self.state, self.action, self.reward, next_state, done))
            
            # st+1 is now our current state
            self.state = next_state

        self.vel_x_old = self.vel_x
        ### LEARNING PART            
        # Obtain random mini-batch from memory
        batch = self.memory.sample(self.batch_size)
        states_mb = np.array([each[0] for each in batch], ndmin=3)
        actions_mb = np.array([each[1] for each in batch])
        rewards_mb = np.array([each[2] for each in batch]) 
        next_states_mb = np.array([each[3] for each in batch], ndmin=3)
        dones_mb = np.array([each[4] for each in batch])

        target_Qs_batch = []

            # Get Q values for next_state 
        Qs_next_state = self.sess.run(self.DQNetwork.output, feed_dict = {self.DQNetwork.inputs_: next_states_mb})
        
        # Set Q_target = r if the episode ends at s+1, otherwise set Q_target = r + gamma*maxQ(s', a')
        for i in range(0, len(batch)):
            terminal = dones_mb[i]

            # If we are in a terminal state, only equals reward
            if terminal:
                target_Qs_batch.append(rewards_mb[i])
                
            else:
                target_ai = rewards_mb[i] + self.gamma * np.max(Qs_next_state[i])
                target_Qs_batch.append(target_ai)
                

        targets_mb = np.array([each for each in target_Qs_batch])

        loss, _ = self.sess.run([self.DQNetwork.loss, self.DQNetwork.optimizer],
                            feed_dict={self.DQNetwork.inputs_: states_mb,
                                        self.DQNetwork.target_Q: targets_mb,
                                        self.DQNetwork.actions_: actions_mb})

        # Write TF Summaries
        summary = self.sess.run(self.write_op, feed_dict={self.DQNetwork.inputs_: states_mb,
                                            self.DQNetwork.target_Q: targets_mb,
                                            self.DQNetwork.actions_: actions_mb})
        self.writer.add_summary(summary,1)
        self.writer.flush()
        self.reward = 0

    def prepare_new_round(self, goal, ball, keeper):

        done = 1

        if(not goal):
            self.reward += 1

        self.episode_rewards.append(self.reward)

        #self.bk.resetCoordinates()

        # the episode ends so no next state
        next_state = np.zeros((4), dtype= np.float)
        next_state, self.stacked_states = stack_states(self.stacked_states, next_state, False, self.stack_size)

        # Set step = max_steps to end the episode
        self.step = self.max_steps

        # Get the total reward of the episode
        self.total_reward.append(np.sum(self.episode_rewards))

        episode_rewards = self.episode_rewards

        self.episode_rewards = []
        if self.episode % 500 == 0:
            date_time = datetime.now().strftime("%m-%d-%Y,%H-%M-%S")
            save_path = self.saver.save(self.sess, "AI_models/AI_save_%s_episode_%d.ckpt" % (date_time, self.episode))
            print("AI model saved")
        self.episode += 1

        self.memory.add((self.state, self.action, self.reward, next_state, done))

        self.update_data(done, ball, keeper)
        return episode_rewards, self.total_reward

        

"""
Here we create our environment
"""
def create_environment():
    """Functie om de Box2D environment te creeeren. 
    
    Returns:
        possible_actions (list): lijst van mogelijke acties.
    """
    # game = DoomGame()
    
    # # Load the correct configuration
    # game.load_config("basic.cfg")
    
    # # Load the correct scenario (in our case basic scenario)
    # game.set_doom_scenario_path("basic.wad")
    
    # game.init()
    
    # Here our possible actions
    up = [1, 0, 0, 0]
    down = [0, 1, 0, 0]
    shoot = [0, 0, 1, 0]
    still = [0, 0, 0, 1]
    possible_actions = [up, down, shoot, still]
    
    return possible_actions


def test_environment(self):
    """Performing random action to test the environment
    """
    # game = DoomGame()
    # game.load_config("basic.cfg")
    # game.set_doom_scenario_path("basic.wad")
    # game.init()
    up = [1, 0, 0, 0]
    down = [0, 1, 0, 0]
    shoot = [0, 0, 1, 0]
    still = [0, 0, 0, 1]
    actions = [up, down, shoot, still]
    goals = 0
    blocks = 0

    episodes = 10
    for i in range(episodes):
        # game.new_episode()
        while True:
            new_state = [self.ball.position.x, self.ball.position.y, self.body.position.x, self.body.position.y]
            action = random.choice(actions)
            print(action)
            if(self.goals > goals):
                reward = 100
                goals = self.goals
                break
            if(self.blocks > blocks):
                reward = -100
                blocks = self.blocks
                break
            print ("\treward:", reward)
            time.sleep(0.02)
        print ("Result:", reward)
        time.sleep(2)
    # game.close()



def stack_states(stacked_states, new_state, is_new_episode, stack_size):
    """remember last 4 states in array

    Args:
        stacked_states (deque[4]): deque array van afgelopen laatste 4 states
        new_state (numpy array): numpy array van nieuwe state
        is_new_episode (bool): aangeven of er een nieuwe episode begint
        stack_size (int): hoeveelheid voorgaande states onthouden

    Returns:
        stacked_state (list): @@@
        stacked_states (deque[list]):  @@@
    """
    if is_new_episode:
        # Clear our stacked_states
        stacked_states = deque([np.zeros(4, dtype=np.float) for i in range(stack_size)], maxlen=4) 
        
        # Because we're in a new episode, copy the same frame 4x.
        for i in range(4):
            stacked_states.append(new_state)
        """
        # Oude waarde.
        stacked_states.append(new_state)
        stacked_states.append(new_state)
        stacked_states.append(new_state)
        stacked_states.append(new_state)
        """
        # Stack the frames
        stacked_state = np.stack(stacked_states, axis=1)
        
    else:
        # Append frame to deque, automatically removes the oldest frame
        stacked_states.append(new_state)

        # Build the stacked state (first dimension specifies different frames)
        stacked_state = np.stack(stacked_states, axis=1) 
    
    return stacked_state, stacked_states



class DQNetwork:
    """
    AI funtionaliteiten
    """
    
    def __init__(self, state_size, action_size, learning_rate, name='DQNetwork'):
        """initialiseer AI parameters.
        
        Args:
            state_size (int): hoeveelheid voorgaande states onthouden
            action_size (int): hoeveelheid mogelijke acties voor ai output
            learning_rate (float): leersnelheid tussen ramdom acties en ai gekozen acties
            name (str, optional): scope benaming. Defaults to 'DQNetwork'.
        """
        self.state_size = state_size
        self.action_size = action_size
        self.learning_rate = learning_rate
        
        with tf.variable_scope(name):
            # We create the placeholders
            # *state_size means that we take each elements of state_size in tuple hence is like if we wrote
            # [None, 84, 84, 4]
            self.inputs_ = tf.placeholder(tf.float32, [None, *state_size], name="inputs")
            self.actions_ = tf.placeholder(tf.float32, [None, action_size], name="actions_")
            
            # Remember that target_Q is the R(s,a) + ymax Qhat(s', a')
            self.target_Q = tf.placeholder(tf.float32, [None], name="target")
            
            self.flatten = tf.layers.flatten(self.inputs_)
            
            self.fc = tf.layers.dense(inputs = self.flatten,
                                    units = 16,
                                    activation = tf.nn.elu,
                                    kernel_initializer=tf.contrib.layers.xavier_initializer(),
                                    name="fc1")
            
            
            self.output = tf.layers.dense(inputs = self.fc, 
                                           kernel_initializer=tf.contrib.layers.xavier_initializer(),
                                          units = 4, 
                                        activation=None)

  
            # Q is our predicted Q value.
            self.Q = tf.reduce_sum(tf.multiply(self.output, self.actions_), axis=1)
            
            # The loss is the difference between our predicted Q_values and the Q_target
            # Sum(Qtarget - Q)^2
            self.loss = tf.reduce_mean(tf.square(self.target_Q - self.Q))
            
            self.optimizer = tf.train.RMSPropOptimizer(self.learning_rate).minimize(self.loss)

class Memory():
    """onthoud alle ervaringen.
    """
    def __init__(self, max_size):
        """initialiseer memory grootte. 
        
        Args:
            max_size (int): hoeveelheid laatste acties en states om te onthouden.
        """
        # print(max_size)
        self.buffer = deque(maxlen = max_size)
        # print(len(self.buffer))
    
    def add(self, experience):
        """voeg AI ervaring toe.
        
        Args:
            experience (array[5]): array van (state, action, reward, next_state, done)
        """
        self.buffer.append(experience)
    
    def sample(self, batch_size):
        """haal memory buffer op.
        
        Args:
            batch_size (int): hoeveelheid ervaringen er opgehaalt moeten worden
        
        Returns:
            (deque[4]): deque array van nieuwe laatste 4 states
        """
        buffer_size = len(self.buffer)
        # print(buffer_size)
        # print(buffer_size)
        # print(buffer_size)
        # print(batch_size)
        index = np.random.choice(np.arange(buffer_size),
                                size = batch_size,
                                replace = True)
        
        return [self.buffer[i] for i in index]


def predict_action(explore_start, explore_stop, decay_rate, decay_step, state, actions, sess, DQNetwork):
    """bepaal AI actie of random actie
    
    Args:
        explore_start (float): begin persentage ratio random actie tot AI bepaalde actie
        explore_stop (float): eind persentage ratio random actie tot AI bepaalde actie
        decay_rate (float): snelheid van explore_start tot explore_stop
        decay_step (int): hoeveelheid gemaakte steps
        state (numpy array): numpy array van state
        actions (list): lijst van mogelijke acties voor ai
        sess (tf.Session()): TensorFlow session
        DQNetwork (class): DQNetwork class
    
    Returns:
        action (list): list waarin een boolean aangeeft welke actie genomen dient te worden.
        explore_probability (float): randomwaarde die aangeeft of een randomactie uitgevoerd moet worden.
    """
    # * EPSILON GREEDY STRATEGY
    # Choose action a from state s using epsilon greedy.
    ## First we randomize a number
    exp_exp_tradeoff = np.random.rand()

    # Here we'll use an improved version of our epsilon greedy strategy used in Q-learning notebook
    explore_probability = explore_stop + (explore_start - explore_stop) * np.exp(-decay_rate * decay_step)
    
    if (explore_probability > exp_exp_tradeoff):
        # Make a random action (exploration)
        action = random.choice(actions)
        
    else:
        # Get action from Q-network (exploitation)
        # Estimate the Qs values state
        Qs = sess.run(DQNetwork.output, feed_dict = {DQNetwork.inputs_: state.reshape((1, *state.shape))})
        
        # Take the biggest Q value (= the best action)
        choice = np.argmax(Qs)
        action = actions[int(choice)]
                
    return action, explore_probability
