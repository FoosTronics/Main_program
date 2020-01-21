"""
    Dit bestand betreft de functionaliteit van de AI

    Simuleert de omgeving van de tafelvoetbaltafel met de keeper.
    Deze simulatie is bedoeld om een AI te trainen zodat deze het spel kan spelen

    Gebruik de W,A,S,D toetsen om de keeper te bewegen.
    Druk op C om de simulatie te starten.

    File:
        DeepQLearning.py
    Date:
        20-1-2020
    Version:
        1.12
    Modifier:
        Daniël Boon
    Used_IDE:
        Visual Studio Code (Python 3.6.7 64-bit)
    Schematic:
        Lucidchart: NLE/AI/LLD AI
    Version management:
        1.0:
            Headers up-to-date.
        1.10:
            Docstrings aangepast naar Google-format. 
        1.11:
            Spelling en grammatica commentaren nagekeken
            Engels vertaald naar Nederlands
        1.12:
            state volgorde omgedraait
"""

import tensorflow as tf      # Deep Learning library
import numpy as np           # Matrixen verwerken

import random                # Toepassen van  "random number generation".
import time                  # Toepassen van tijd calculaties.

from collections import deque # Ordered collection with ends
import matplotlib.pyplot as plt # Weergeven van grafieken.
from datetime import datetime


import warnings # Dit zorgt ervoor dat alle waarschuwings berichten, die normaliter worden geprint tijdens de training door skiimage, worden genegeerd.
warnings.filterwarnings('ignore') 

class DQLBase:
    """
    Klasse voor de Deep-Q-Learning.

    **Author**:
        Daniël Boon \n
    **Version**:
        1.11         \n
    **Date**:
        20-1-2020
    """
    def __init__(self, debug=False):
        self.possible_actions = create_environment()

        self.stack_size = 4 # We stack 4 frames

        # Initialiseren van deque met zero-images met één array per afbeelding.
        self.stacked_states = deque([np.zeros(4, dtype=np.float) for i in range(self.stack_size)], maxlen=4) 

        ### MODEL HYPERPARAMETERS
        # De input is een stack van 4 frames, daarom 84x84x4 (Breedte, hoogte, kanalen).
        state_size = [4, 4]
        action_size = 4  # game.get_available_buttons_size()              # 3 mogelijke acties: links, rechts, schieten
        #TODO: was 0.0002
        learning_rate = 0.01      # Alpha (aka leer ratio)

        ### TRAINING HYPERPARAMETERS
        total_episodes = 500        # Totaal aantal episodes per training .
        self.max_steps = 1000              # Maximaal aantal stappen in een episode.
        #TODO: was 64
        self.batch_size = 32

        # Paramaters voor het verkennen van de Epsilon Greedy strategie.
        #TODO: explore_start was 1.0
        # self.explore_start = 1.0            # De kans op verkenning bij de start
        self.explore_start = 0.0            # De kans op verkenning bij de start
        self.explore_stop = 0.01            # De minimale kans op verkenning
        self.decay_rate = 0.0001            # De exponentiele verval ratio voor de kans op verkennen

        # Q learning hyperparameters
        self.gamma = 0.95               # Waardeverminderings ratio

        ### MEMORY HYPERPARAMETERS
        # Aantal ervaringen die worden opgeslagen in het geheugen wanneer er voor het eerst wordt geinitialiseerd.
        pretrain_length = self.batch_size
        memory_size = 10000          # Aantal ervaringen dat het geheugen kan bewaren.
       
        ### MODIFY THIS TO FALSE IF YOU JUST WANT TO SEE THE TRAINED AGENT
        training = True

        ## Verander naar TRUE als je de Environment wilt renderen
        episode_render = False

        # Herstellen van de grafiek
        tf.reset_default_graph()

        # Instantieren van het DQNetwork
        self.DQNetwork = DQNetwork(state_size, action_size, learning_rate)
        
        # Instantieer het geheugen
        self.memory = Memory(max_size = memory_size)

        # Setup TensorBoard Writer
        self.writer = tf.summary.FileWriter("/tensorboard/dqn/1")

        ## Verliezen
        tf.summary.scalar("Loss", self.DQNetwork.loss)

        self.write_op = tf.summary.merge_all()

        # Saver helpt bij het bewaren van het model.
        self.saver = tf.train.Saver()

        # Met tf.Session() als self.sess:
        self.sess = tf.Session()
        # Initialiseer de variabelen.
        self.sess.run(tf.global_variables_initializer())
        
        # Initialiseer de afname ratio (dat wordt gebruikt om Epsilon te verminderen). 
        self.decay_step = 0
                    # Zet stap naar 0.
        self.step = 0
        
        # Initialiseer de beloningen van de episode.
        self.episode_rewards = []

        # Maak een nieuwe episode en observeer de eerste toestand.
        # game.new_episode()
        self.state = np.array([0, 0, 0, 0])
        
        # Onthoud dat de stack frame functie ook de preprocess functie aanroept. 
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
        """De AI besluit wat voor acties moeten worden genomen.
        
        Returns:
            (tuple) action, old_action, target, vel_x, old_vel_x
        """
        for i in range(len(self.state[0])-1):
            self.vel_x = self.state[0][i+1] - self.state[0][i]
            self.vel_y = self.state[1][i+1] - self.state[1][i]

        target = self.state[1][3]+(((-16.72-self.state[0][3])/self.vel_x) * self.vel_y)

        if((self.vel_x > 0) or (target > 11.26) or (target < 6.16)):
            target = np.nan

        done = 0
        old_action = self.action

        action, explore_probability = predict_action(self.explore_start, self.explore_stop, self.decay_rate, self.decay_step, self.state, self.possible_actions, self.sess, self.DQNetwork)
        self.action = action
        if (not np.isnan(target)):
            if (np.array_equal(action, self.possible_actions[0])):
                if(target > self.state[3][3]):
                    self.reward += 0.2*abs(self.state[3][3]-target)
                else:
                    self.reward -= 0.05*(5.1-abs(self.state[3][3]-target))

            elif np.array_equal(action, self.possible_actions[1]):
                if(target < self.state[3][3]):
                    self.reward += 0.2*abs(self.state[3][3]-target)
                else:
                    self.reward -= 0.05*(5.1-abs(self.state[3][3]-target))

        if np.array_equal(action, self.possible_actions[2]):
            if( (self.state[0][3] > -16) and (self.state[0][3] < -14) and (abs(self.state[3][3]-self.state[1][3]) < 0.37)):
                self.reward += 0.5
            else:
                self.reward -= 0.1
        
        if np.array_equal(action, self.possible_actions[3]):
            if(np.isnan(target)):
                self.reward += 0.01
            elif(abs(self.state[1][3]-target) < 0.37):
                self.reward += 0.3
            else:
                self.reward -= 0.05



        return action, old_action, target, self.vel_x, self.vel_x_old

    def update_data(self, done, ball, keeper):
        """Update de data naar de memory klasse.
        
        Args:
            done: (bool) controleert of de ronde is afgelopen.   
            ball: (tuple) coördinaten van de bal. 
            keeper: (tuple) coördinaten van de keeper.
        """
        if(not done):
            self.episode_rewards.append(self.reward)
            # Verkrijg de volgende staat.
            next_state =  np.array([ball.position.x, ball.position.y, keeper.position.x, keeper.position.y])
            
            # Stapel het frame van de next_state op
            next_state, self.stacked_states = stack_states(self.stacked_states, next_state, False, self.stack_size)
            

            # Voeg een ervaring toe aan het geheugen.
            self.memory.add((self.state, self.action, self.reward, next_state, done))
            
            # st+1 is nu de huidige staat.
            self.state = next_state

        self.vel_x_old = self.vel_x
        ### LEER GEDEELTE        
        # Verkrijg willekeurige mini-batch van het geheugen .
        batch = self.memory.sample(self.batch_size)
        states_mb = np.array([each[0] for each in batch], ndmin=3)
        actions_mb = np.array([each[1] for each in batch])
        rewards_mb = np.array([each[2] for each in batch]) 
        next_states_mb = np.array([each[3] for each in batch], ndmin=3)
        dones_mb = np.array([each[4] for each in batch])

        target_Qs_batch = []

            # Verkrijg Q-waardes voor de next_state.
        Qs_next_state = self.sess.run(self.DQNetwork.output, feed_dict = {self.DQNetwork.inputs_: next_states_mb})
        
        # Zet Q_target =r als de episode eindigd op s+1, anders zet Q_target = r + gamma*maxQ(s', a').
        for i in range(0, len(batch)):
            terminal = dones_mb[i]

            # Als we in een terminale staat belanden, only is gelijk aan reward.
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
        """Zorgt dat de AI wordt klaargemaakt voor een nieuwe ronde. 

        Args:
            goals: (bool) checkt of de ronde is afgelopen.
            ball: (tuple) positie van de bal.
            keeper: (tuple) positie van de keeper.
        returns:
            (tuple) episode_rewards, total_reward - rewards die de ronde zijn behaald. Totale rewards die de AI behaald heeft.
        """
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
            print("AI model opgeslagen")
        self.episode += 1

        self.memory.add((self.state, self.action, self.reward, next_state, done))

        self.update_data(done, ball, keeper)
        return episode_rewards, self.total_reward

        

"""
Hier maken we onze Environment.
"""
def create_environment():
    """Functie om de Box2D environment te creëeren. 
    
    Returns:
        possible_actions: (list) lijst van mogelijke acties.
    """
    # game = DoomGame()
    
    # # Laad de correcte configuratie.
    # game.load_config("basic.cfg")
    
    # # Laad het correcte scenario (in ons geval de basic scenario).
    # game.set_doom_scenario_path("basic.wad")
    
    # game.init()
    
    # Hier zijn de mogelijke acties.
    up = [1, 0, 0, 0]
    down = [0, 1, 0, 0]
    shoot = [0, 0, 1, 0]
    still = [0, 0, 0, 1]
    possible_actions = [up, down, shoot, still]
    
    return possible_actions


def test_environment(self):
    """ Voer willekeurige acties uit om de Environment te testen.
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
        print ("Resultaat:", reward)
        time.sleep(2)
    # game.close()



def stack_states(stacked_states, new_state, is_new_episode, stack_size):
    """ Onthoudt de laatste 4 statussen in een array.

    Args:
        stacked_states: (deque[4]) deque array van afgelopen laatste 4 states
        new_state: (numpy array) numpy array van nieuwe state
        is_new_episode: (bool) aangeven of er een nieuwe episode begint
        stack_size: (int) hoeveelheid voorgaande states onthouden

    Returns:
        stacked_state: (list) @@@
        stacked_states: (deque[list])  @@@
    """
    if is_new_episode:
        # Maak de stacked_states leeg.
        stacked_states = deque([np.zeros(4, dtype=np.float) for i in range(stack_size)], maxlen=4) 
        
        # Omdat we in een nieuwe episode zijn, kopieer hetzelfde frame 4x.
        for i in range(4):
            stacked_states.append(new_state)
        """
        # Oude waarde.
        stacked_states.append(new_state)
        stacked_states.append(new_state)
        stacked_states.append(new_state)
        stacked_states.append(new_state)
        """
        # Stapel de frames op.
        stacked_state = np.stack(stacked_states, axis=1)
        
    else:
        # Pas de frames toe op deque, dit verwijdert automatisch het oudste frame.
        stacked_states.append(new_state)

        # Bouw op de opgestapelde staat. De eerste dimensie specificeert verschillende frames. 
        stacked_state = np.stack(stacked_states, axis=1) 
    
    return stacked_state, stacked_states



class DQNetwork:
    """
    Klasse voor het opbouwen van het neurale netwerk. 

    **Author**:
        Daniël Boon \n
    **Version**:
        1.11        \n
    **Date**:
       20-1-2020
    """
    
    def __init__(self, state_size, action_size, learning_rate, name='DQNetwork'):
        """initialiseer AI parameters.
        
        Args:
            state_size: (int) hoeveelheid voorgaande states onthouden
            action_size: (int) hoeveelheid mogelijke acties voor AI output
            learning_rate: (float) leersnelheid tussen ramdom acties en AI gekozen acties
            name: (str, optional) scope benaming. Standaard 'DQNetwork'.
        """
        self.state_size = state_size
        self.action_size = action_size
        self.learning_rate = learning_rate
        
        with tf.variable_scope(name):
            # Het creëren van de plaatshouder.
            # *state_size betekent dat we elk element van state_sizee in tuple pakken. 
            # [None, 84, 84, 4]
            self.inputs_ = tf.placeholder(tf.float32, [None, *state_size], name="inputs")
            self.actions_ = tf.placeholder(tf.float32, [None, action_size], name="actions_")
            
            # Onthoud dat target_q de R(s,a) + ymax Qhat(s', a') is.
            self.target_Q = tf.placeholder(tf.float32, [None], name="target")
            
            self.flatten = tf.layers.flatten(self.inputs_)
            
            # Laag 1
            self.fc = tf.layers.dense(inputs = self.flatten,
                                    units = 16,
                                    activation = tf.nn.elu,
                                    kernel_initializer=tf.contrib.layers.xavier_initializer(),
                                    name="fc1")
            
            
            self.output = tf.layers.dense(inputs = self.fc, 
                                           kernel_initializer=tf.contrib.layers.xavier_initializer(),
                                          units = 4, 
                                        activation=None)

  
            #  Q is onze voorspelde Q-waarde.
            self.Q = tf.reduce_sum(tf.multiply(self.output, self.actions_), axis=1)
            
            #  Het verlies is het verschil tussen de voorspelde Q_values en de Q_target.
            # Sum(Qtarget - Q)^2
            self.loss = tf.reduce_mean(tf.square(self.target_Q - self.Q))
            
            self.optimizer = tf.train.RMSPropOptimizer(self.learning_rate).minimize(self.loss)

class Memory():
    """Onthoud alle AI ervaringen.

    **Author**:
        Daniël Boon \n
    **Version**:
        1.11        \n
    **Date**:
       20-1-2020
    """
    def __init__(self, max_size):
        """Initialiseer geheugen grootte. 
        
        Args:
            max_size: (int) hoeveelheid laatste acties en states om te onthouden.
        """
        # print(max_size)
        self.buffer = deque(maxlen = max_size)
        # print(len(self.buffer))
    
    def add(self, experience):
        """voeg AI ervaring toe.
        
        Args:
            experience: (array[5]) array van (state, action, reward, next_state, done)
        """
        self.buffer.append(experience)
    
    def sample(self, batch_size):
        """Haal geheugen buffer op.
        
        Args:
            batch_size: (int) hoeveelheid ervaringen er opgehaalt moeten worden
        
        Returns:
            (deque[4]) deque array van nieuwe laatste 4 states
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
    """Bepaal AI actie of random actie
    
    Args:
        explore_start: (float) begin percentage ratio random actie tot AI bepaalde actie.
        explore_stop: (float) eind percentage ratio random actie tot AI bepaalde actie.
        decay_rate: (float) snelheid van explore_start tot explore_stop.
        decay_step: (int) hoeveelheid gemaakte stappen.
        state: (numpy array) numpy array van state.
        actions: (list) lijst van mogelijke acties voor ai.
        sess: (tf.Session()) TensorFlow session.
        DQNetwork: (class) DQNetwork klasse.
    
    Returns:
        action: (list) lijst waarin een boolean aangeeft welke actie genomen dient te worden.
        explore_probability: (float) willekeurige waarde die aangeeft of een willekeurige actie uitgevoerd moet worden.
    """
    # * EPSILON GREEDY STRATEGY
    # Kies actie a van state s met behulp van Epsilon Greedy.
    ## Eerst zorgen we voor een willekeurig nummer.
    exp_exp_tradeoff = np.random.rand()

    # Hier gebruiken we een verbeterde versie van de Epsilon Greedy strategie dat gebruikt wordt in Q-learning notebook.
    explore_probability = explore_stop + (explore_start - explore_stop) * np.exp(-decay_rate * decay_step)
    
    if (explore_probability > exp_exp_tradeoff):    # Ga verkennen.
        # Maak een willekeurige actie(verkennend)
        action = random.choice(actions) 
    else:                                           # Voer voorspelling uit.
        # Verkrijg een actie van Q-network (exploitatie)
        # Schat de Qs values state
        Qs = sess.run(DQNetwork.output, feed_dict = {DQNetwork.inputs_: state.reshape((1, *state.shape))})
        
        # Pak de grootste Q-waarde (= de beste actie)
        choice = np.argmax(Qs)
        action = actions[int(choice)]
                
    return action, explore_probability
