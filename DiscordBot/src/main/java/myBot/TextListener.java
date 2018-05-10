package myBot;

import net.dv8tion.jda.core.entities.Guild;
import net.dv8tion.jda.core.entities.Message;
import net.dv8tion.jda.core.entities.MessageChannel;
import net.dv8tion.jda.core.events.ReadyEvent;
import net.dv8tion.jda.core.events.message.MessageReceivedEvent;
import net.dv8tion.jda.core.hooks.ListenerAdapter;


public class TextListener extends ListenerAdapter{
	
	@Override
	public void onReady(ReadyEvent event) {
		String out="El bot está funcionando en los servidores: \n";
		
		String[] array= {
				"Sorpresa, he vuelto",
				"Ya estoy aqui",
				"Hey chicos, he vuelto y no en forma de chapas :D",
				"Hola guapos, me echábais de menos?",
				"POOPOPOPOPOPOPOPOPOPOPOPO",
				"Somos blancos somos verdes, somos negros y amarillos, somos todos diferentes, estamos muy unidoooos",
				"La espada invisible es la más mortífera",
				"Ey muy buenas a todos GUAPÍSIMOS",
				"Como quisiera podeeer viviiir sin aaaaire",
				
				
				};
		int i=(int)(Math.random()*array.length);
		System.out.println(i);
		String msg=array[i];
		
		for(Guild g : event.getJDA().getGuilds()) {
			out+="name "+g.getName()+"		id: "+g.getId()+"\n";
			g.getTextChannels().get(1).sendMessage(
					msg
					).queue();
		}
		
		System.out.println(out);
		
	}
	
	    @Override
	    public void onMessageReceived(MessageReceivedEvent event)
	    {
	        if (event.getAuthor().isBot()) return;
	        // We don't want to respond to other bot accounts, including ourself
	        else {
	        Message message = event.getMessage();
	        String content = message.getContentRaw(); 
	        // getContentRaw() is an atomic getter
	        // getContentDisplay() is a lazy getter which modifies the content for e.g. console view (strip discord formatting)
	        if (content.equalsIgnoreCase("!ping")){
	            MessageChannel channel = event.getChannel();
	            channel.sendMessage("Pong!").queue(); // Important to call .queue() on the RestAction returned by sendMessage(...)
	        }
	        }
	    }
	   
}
