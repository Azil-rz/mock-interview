import computerNetwork from './ComputerNetworkQuestions.json';
import frontEnd from './FrontEndQuestions.json';
import operatingSystem from './computer_operating_system.json';
import network from './computer_network.json';

const categories = {
    'Computer Network': computerNetwork.questions,
    'Front End': frontEnd.questions,
    'Operating System': operatingSystem.questions,
    'Network': network.questions,
};

export default categories;
