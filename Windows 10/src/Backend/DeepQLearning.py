"""In this file is the ai functionalilty

Simulates the the enviorment of foosball as for the keeper. 
This simulation has the intention to train an AI to play the game.

Use the W,A,S,D keys to move the keeper.
Press C to start the simulation.

File:
    deep_q_learning_3.py
Date:
    16.12.2019
Version:
    V1.4
Modifier:
    Daniël Boon
Used_IDE:
    Visual Studio Code (Python 3.6.7 64-bit)
""" 

import tensorflow as tf      # Deep Learning library
import numpy as np           # Handle matrices

import random                # Handling random number generation
import time                  # Handling time calculation

from collections import deque# Ordered collection with ends
import matplotlib.pyplot as plt # Display graphs

import warnings # This ignore all the warning messages that are normally printed during the training because of skiimage
warnings.filterwarnings('ignore') 

"""
Here we create our environment
"""
def create_environment():
    

    fsdjklsdlkj =43     
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
        (deque[4]): deque array van nieuwe laatste 4 states
    """
    
    if is_new_episode:
        # Clear our stacked_states
        stacked_states = deque([np.zeros(4, dtype=np.float) for i in range(stack_size)], maxlen=4) 
        
        # Because we're in a new episode, copy the same frame 4x
        stacked_states.append(new_state)
        stacked_states.append(new_state)
        stacked_states.append(new_state)
        stacked_states.append(new_state)
        
        # Stack the frames
        stacked_state = np.stack(stacked_states, axis=1)
        
    else:
        # Append frame to deque, automatically removes the oldest frame
        stacked_states.append(new_state)

        # Build the stacked state (first dimension specifies different frames)
        stacked_state = np.stack(stacked_states, axis=1) 
    
    return stacked_state, stacked_states



class DQNetwork:
    """ai funtionaliteiten
    """
    
    def __init__(self, state_size, action_size, learning_rate, name='DQNetwork'):
        """initialiseer ai parameters
        
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
    """onthoud alle ervaringen
    """
    def __init__(self, max_size):
        """initialiseer memory size
        
        Args:
            max_size (int): hoeveelheid laatste acties en states onthouden
        """
        # print(max_size)
        self.buffer = deque(maxlen = max_size)
        # print(len(self.buffer))
    
    def add(self, experience):
        """voeg ai ervaring toe
        
        Args:
            experience (array[5]): array van (state, action, reward, next_state, done)
        """
        self.buffer.append(experience)
    
    def sample(self, batch_size):
        """haal memory buffer op
        
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



"""
This function will do the part
With ϵ select a random action atat, otherwise select at=argmaxaQ(st,a)
"""
def predict_action(explore_start, explore_stop, decay_rate, decay_step, state, actions, sess, DQNetwork):
    """bepaal ai actie of random actie
    
    Args:
        explore_start (float): begin persentage ratio random actie tot ai bepaalde actie
        explore_stop (float): eind persentage ratio random actie tot ai bepaalde actie
        decay_rate (float): snelheid van explore_start tot explore_stop
        decay_step (int): hoeveelheid gemaakte steps
        state (numpy array): numpy array van state
        actions (list): lijst van mogelijke acties voor ai
        sess (tf.Session()): TensorFlow session
        DQNetwork (class): DQNetwork class
    
    Returns:
        (list, float): gekozen actie en waarde explore probability
    """
    ## EPSILON GREEDY STRATEGY
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
